from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import math

class OrToolsSolver:
    @staticmethod
    def solve(vroom_input_json):
        data = vroom_input_json
        vehicles = data['vehicles']
        shipments = data['shipments']
        
        # 假设卡车平均速度 (km/h)
        TRUCK_SPEED_KMH = 75.0 

        # --- 1. 节点与坐标映射 ---
        locations = []
        # 安全检查：确保有车辆数据
        if not vehicles:
            print("⚠️ 错误：没有车辆数据")
            return {"routes": []}

        depot_loc = vehicles[0]['start'] 
        locations.append(depot_loc) 
        
        pickup_indices = []
        delivery_indices = []
        
        for s in shipments:
            locations.append(s['pickup']['location'])   
            pickup_indices.append(len(locations) - 1)
            locations.append(s['delivery']['location']) 
            delivery_indices.append(len(locations) - 1)

        # --- 2. 距离与时间计算 (内嵌简易计算) ---
        def get_dist_meter(i, j):
            l1, l2 = locations[i], locations[j]
            # 简易欧式距离估算经纬度距离
            dist_km = math.hypot(l1[0]-l2[0], l1[1]-l2[1]) * 111
            return int(dist_km * 1000)

        def get_time_min(i, j):
            dist_m = get_dist_meter(i, j)
            dist_km = dist_m / 1000
            return int((dist_km / TRUCK_SPEED_KMH) * 60)

        # --- 3. 初始化 OR-Tools 模型 ---
        manager = pywrapcp.RoutingIndexManager(len(locations), len(vehicles), 0)
        routing = pywrapcp.RoutingModel(manager)

        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return get_dist_meter(from_node, to_node)

        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index) 

        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            travel_time = get_time_min(from_node, to_node)
            service_time = 30 if from_node != 0 else 0
            return travel_time + service_time

        time_callback_index = routing.RegisterTransitCallback(time_callback)

        # --- 4. 维度设置 ---
        
        # 4.1 重量与体积维度
        def add_capacity_dimension(dim_name, item_idx):
            def capacity_callback(from_index):
                node = manager.IndexToNode(from_index)
                if node == 0: return 0
                s_idx = (node - 1) // 2
                is_pickup = (node - 1) % 2 == 0
                val = shipments[s_idx]['amount'][item_idx]
                return val if is_pickup else -val 

            callback_index = routing.RegisterUnaryTransitCallback(capacity_callback)
            routing.AddDimensionWithVehicleCapacity(
                callback_index, 0, 
                [v['capacity'][item_idx] for v in vehicles], 
                True, dim_name
            )

        add_capacity_dimension("Weight", 0)
        add_capacity_dimension("Volume", 1)

        # 4.2 时间维度 (Time) - 增加负载均衡
        routing.AddDimension(
            time_callback_index,
            24 * 60 * 30, # Max time
            24 * 60 * 30, 
            False,        
            "Time"
        )
        time_dim = routing.GetDimensionOrDie("Time")
        time_dim.SetGlobalSpanCostCoefficient(100) 

        # --- 5. 约束设置 ---
        distance_dimension = routing.GetDimensionOrDie('Weight')
        
        for i in range(len(shipments)):
            p_index = manager.NodeToIndex(pickup_indices[i])
            d_index = manager.NodeToIndex(delivery_indices[i])
            routing.AddPickupAndDelivery(p_index, d_index)
            routing.solver().Add(routing.VehicleVar(p_index) == routing.VehicleVar(d_index))
            routing.solver().Add(distance_dimension.CumulVar(p_index) <= distance_dimension.CumulVar(d_index))

        # 强制 LIFO
        routing.SetPickupAndDeliveryPolicyOfAllVehicles(pywrapcp.RoutingModel.PICKUP_AND_DELIVERY_LIFO)

        # --- 5.5 技能约束 ---
        print("\n=== [开始校验技能兼容性] ===")
        for s_idx, shipment in enumerate(shipments):
            raw_req = shipment.get('skills', [])
            req_skills = set(str(s).strip().lower() for s in raw_req if s)
            
            if not req_skills:
                continue
            
            p_index = manager.NodeToIndex(pickup_indices[s_idx])
            d_index = manager.NodeToIndex(delivery_indices[s_idx])
            
            compatible_vehicles = []
            for v_idx, vehicle in enumerate(vehicles):
                raw_veh_skills = vehicle.get('skills', [])
                veh_skills = set(str(v).strip().lower() for v in raw_veh_skills if v)
                
                if req_skills.issubset(veh_skills):
                    compatible_vehicles.append(int(v_idx)) 

            if not compatible_vehicles:
                print(f"❌ [跳过] 订单 #{shipment['id']} ({req_skills}) 无匹配车辆，将无法被服务。")
                continue 

            try:
                routing.VehicleVar(p_index).SetValues(compatible_vehicles)
                routing.VehicleVar(d_index).SetValues(compatible_vehicles)
                print(f"   🔒 订单 #{shipment['id']} 已强制绑定给车辆索引: {compatible_vehicles}")
            except Exception as e:
                print(f"⚠️ 设置约束失败: {e}")

        print("==============================\n")

        # --- 6. 求解 ---
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        search_parameters.time_limit.seconds = 5 

        print("   [算法核心] 开始搜索最优路径 (含负载均衡策略)...")
        solution = routing.SolveWithParameters(search_parameters)

        if not solution:
            print("⚠️ 算法未找到可行解！")
            return {"routes": []}
            
        # --- 7. 结果生成 ---
        print("✅ 成功找到方案！正在生成报表...")
        routes_json = []
        weight_dim = routing.GetDimensionOrDie("Weight")
        vol_dim = routing.GetDimensionOrDie("Volume")
        
        for vehicle_id in range(len(vehicles)):
            index = routing.Start(vehicle_id)
            if routing.IsEnd(solution.Value(routing.NextVar(index))):
                continue 
                
            steps = []
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                arrival_load_w = solution.Value(weight_dim.CumulVar(index))
                arrival_load_v = solution.Value(vol_dim.CumulVar(index))
                arrival_time_min = solution.Value(time_dim.CumulVar(index))
                
                step_type = "start"
                order_id_display = "-" 
                change_w = 0
                change_v = 0

                if node_index != 0:
                    s_idx = (node_index - 1) // 2
                    is_pickup = (node_index - 1) % 2 == 0
                    step_type = "pickup" if is_pickup else "delivery"
                    order_id_display = shipments[s_idx]['id']
                    
                    order_amt = shipments[s_idx]['amount']
                    if is_pickup:
                        change_w = order_amt[0]
                        change_v = order_amt[1]
                    else:
                        change_w = -order_amt[0]
                        change_v = -order_amt[1]

                final_load_w = arrival_load_w + change_w
                final_load_v = arrival_load_v + change_v
                
                day = arrival_time_min // (24 * 60)
                hour = (arrival_time_min % (24 * 60)) // 60
                minute = arrival_time_min % 60
                time_str = f"D{day+1} {hour:02d}:{minute:02d}"
                
                steps.append({
                    "type": step_type,
                    "location": locations[node_index],
                    "load": [final_load_w, final_load_v],
                    "arrival": time_str,
                    "order_id": order_id_display
                })
                
                index = solution.Value(routing.NextVar(index))

            steps.append({"type": "end", "location": locations[0], "load": [0,0], "arrival": "End", "order_id": "-"})
            
            routes_json.append({
                "vehicle": vehicles[vehicle_id]['id'],
                "distance": 0,
                "steps": steps
            })
            
        return {"routes": routes_json}