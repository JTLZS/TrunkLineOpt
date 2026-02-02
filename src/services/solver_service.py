from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import math

class OrToolsSolver:
    @staticmethod
    def solve(vroom_input_json):
        data = vroom_input_json
        vehicles = data['vehicles']
        shipments = data['shipments']
        
        # --- 干线场景配置 ---
        TRUCK_SPEED_KMH = 70.0  # 干线平均车速 (考虑高速)
        DEFAULT_SERVICE_TIME = 60 # 干线装卸货通常较久 (分钟)

        if not vehicles or not shipments:
            print("⚠️ 数据为空，无法计算")
            return {"routes": []}

        # --- 1. 坐标索引映射 ---
        locations = []
        # 以第一辆车的起点作为虚拟 Depot (注意：多车场需扩展)
        depot_loc = vehicles[0]['start'] 
        locations.append(depot_loc) 
        
        pickup_indices = []
        delivery_indices = []
        
        for s in shipments:
            locations.append(s['pickup']['location'])   
            pickup_indices.append(len(locations) - 1)
            locations.append(s['delivery']['location']) 
            delivery_indices.append(len(locations) - 1)

        manager = pywrapcp.RoutingIndexManager(len(locations), len(vehicles), 0)
        routing = pywrapcp.RoutingModel(manager)

        # --- 2. 基础计算函数 (距离/时间) ---
        def get_dist_km(i, j):
            l1, l2 = locations[i], locations[j]
            # 干线主要看长距离，欧氏距离 x 系数 模拟路网
            # 111km/度 * 1.2 (路网曲折系数)
            return math.hypot(l1[0]-l2[0], l1[1]-l2[1]) * 111 * 1.2

        def get_time_min(i, j):
            dist = get_dist_km(i, j)
            return int((dist / TRUCK_SPEED_KMH) * 60)

        # --- 3. 成本矩阵 (关键升级：异构车队成本) ---
        # 为每辆车注册独立的成本计算逻辑
        
        for v_idx, vehicle_data in enumerate(vehicles):
            cost_coeff = vehicle_data.get('cost_per_km', 1.0)
            
            def vehicle_cost_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                dist = get_dist_km(from_node, to_node)
                # 成本 = 距离 * 车辆单价 (例如: 1000km * 3元/km = 3000成本)
                return int(dist * cost_coeff)
            
            transit_callback_index = routing.RegisterTransitCallback(vehicle_cost_callback)
            routing.SetArcCostEvaluatorOfVehicle(transit_callback_index, v_idx)
            
            # 设置车辆固定成本 (启动费)
            # 如果这辆车只要动了，就先加固定成本 (如500元)
            fixed_cost = vehicle_data.get('fixed_cost', 0)
            routing.SetFixedCostOfVehicle(fixed_cost, v_idx)

        # --- 4. 维度约束 ---

        # 4.1 容量 (重量 & 体积)
        def create_capacity_dim(name, key_idx):
            def cap_callback(from_index):
                node = manager.IndexToNode(from_index)
                if node == 0: return 0
                s_idx = (node - 1) // 2
                is_pickup = (node - 1) % 2 == 0
                val = shipments[s_idx]['amount'][key_idx]
                return val if is_pickup else -val 

            cb_idx = routing.RegisterUnaryTransitCallback(cap_callback)
            routing.AddDimensionWithVehicleCapacity(
                cb_idx, 0, 
                [v['capacity'][key_idx] for v in vehicles], 
                True, name
            )
        
        create_capacity_dim("Weight", 0)
        create_capacity_dim("Volume", 1)

        # 4.2 时间维度 (关键升级：软时间窗)
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            travel = get_time_min(from_node, to_node)
            # 只有在装货/卸货点才消耗服务时间，Depot不消耗
            service = 0
            if from_node != 0:
                service = DEFAULT_SERVICE_TIME
            return travel + service

        time_cb_idx = routing.RegisterTransitCallback(time_callback)
        routing.AddDimension(
            time_cb_idx,
            24 * 60 * 7, # Max slack (最大允许等待/空闲时间)
            24 * 60 * 5, # Max total time (单车最大行程5天)
            False, "Time"
        )
        time_dim = routing.GetDimensionOrDie("Time")

        # --- 5. 业务约束实现 ---

        # 5.1 P&D 绑定与 LIFO
        dist_dim = routing.GetDimensionOrDie('Weight') # 用于辅助P&D逻辑
        
        for i in range(len(shipments)):
            p_index = manager.NodeToIndex(pickup_indices[i])
            d_index = manager.NodeToIndex(delivery_indices[i])
            
            # 必须由同一辆车完成
            routing.AddPickupAndDelivery(p_index, d_index)
            routing.solver().Add(routing.VehicleVar(p_index) == routing.VehicleVar(d_index))
            routing.solver().Add(dist_dim.CumulVar(p_index) <= dist_dim.CumulVar(d_index))

            # [新增] 软时间窗约束
            # 如果订单有截止时间要求 (例如：要求48小时内送到)
            deadline = shipments[i].get('deadline_min')
            penalty = shipments[i].get('penalty', 100)
            
            if deadline is not None and deadline > 0:
                # 对 Delivery 节点设置软上限
                # 含义：尽量在 deadline 前送到。如果不得不晚到，按 penalty 系数增加总成本
                time_dim.SetCumulVarSoftUpperBound(d_index, deadline, penalty)

        # 强制 LIFO (干线必须，防止翻仓)
        routing.SetPickupAndDeliveryPolicyOfAllVehicles(pywrapcp.RoutingModel.PICKUP_AND_DELIVERY_LIFO)

        # 5.2 技能匹配 (沿用)
        for s_idx, shipment in enumerate(shipments):
            req_skills = set(shipment.get('skills', []))
            if not req_skills: continue
            
            p_index = manager.NodeToIndex(pickup_indices[s_idx])
            d_index = manager.NodeToIndex(delivery_indices[s_idx])
            
            compatible = []
            for v_idx, vehicle in enumerate(vehicles):
                veh_skills = set(vehicle.get('skills', []))
                if req_skills.issubset(veh_skills):
                    compatible.append(v_idx)
            
            if not compatible:
                print(f"❌ 订单 {shipment['id']} 无匹配技能车辆！")
            else:
                routing.VehicleVar(p_index).SetValues(compatible)
                routing.VehicleVar(d_index).SetValues(compatible)

        # --- 6. 求解与搜索策略 ---
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        # Guided Local Search 是处理此类复杂约束最强大的策略
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
        search_parameters.time_limit.seconds = 5
        # 启用日志便于调试
        # search_parameters.log_search = True 

        print(f"   [算法核心] 启动计算 (车辆数:{len(vehicles)}, 订单数:{len(shipments)})...")
        solution = routing.SolveWithParameters(search_parameters)

        if not solution:
            print("⚠️ 算法未找到可行解！")
            return {"routes": []}

        # --- 7. 结果提取 ---
        return extract_solution(manager, routing, solution, vehicles, locations, shipments, time_dim)

def extract_solution(manager, routing, solution, vehicles, locations, shipments, time_dim):
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
            time_val = solution.Value(time_dim.CumulVar(index))
            load_w = solution.Value(weight_dim.CumulVar(index))
            load_v = solution.Value(vol_dim.CumulVar(index))
            
            step_type = "start"
            oid = "-"
            
            if node_index != 0:
                s_idx = (node_index - 1) // 2
                is_pickup = (node_index - 1) % 2 == 0
                step_type = "pickup" if is_pickup else "delivery"
                oid = shipments[s_idx]['id']

            # 格式化时间 D1 HH:MM
            day = time_val // (24 * 60)
            hour = (time_val % (24 * 60)) // 60
            minute = time_val % 60
            time_str = f"D{day+1} {hour:02d}:{minute:02d}"

            steps.append({
                "type": step_type,
                "location": locations[node_index],
                "load": [load_w, load_v],
                "arrival": time_str,
                "order_id": oid
            })
            
            index = solution.Value(routing.NextVar(index))
        
        # End node
        steps.append({"type": "end", "location": locations[0], "load": [0,0], "arrival": "End", "order_id": "-"})
        routes_json.append({"vehicle": vehicles[vehicle_id]['id'], "steps": steps})
        
    return {"routes": routes_json}