from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import math

class OrToolsSolver:
    @staticmethod
    def solve(vroom_input_json):
        data = vroom_input_json
        vehicles = data['vehicles']
        shipments = data['shipments']
        
        TRUCK_SPEED_KMH = 70.0  
        DEFAULT_SERVICE_TIME = 60 

        if not vehicles or not shipments:
            print("⚠️ 数据为空，无法计算")
            return {"routes": []}

        # --- 1. 坐标索引映射 ---
        locations = []
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

        # --- 2. 基础计算函数 ---
        def get_dist_km(i, j):
            l1, l2 = locations[i], locations[j]
            return math.hypot(l1[0]-l2[0], l1[1]-l2[1]) * 111 * 1.2

        def get_time_min(i, j):
            dist = get_dist_km(i, j)
            return int((dist / TRUCK_SPEED_KMH) * 60)

        # --- 3. 成本矩阵 ---
        for v_idx, vehicle_data in enumerate(vehicles):
            cost_coeff = vehicle_data.get('cost_per_km', 1.0)
            
            def vehicle_cost_callback(from_index, to_index):
                from_node = manager.IndexToNode(from_index)
                to_node = manager.IndexToNode(to_index)
                dist = get_dist_km(from_node, to_node)
                return int(dist * cost_coeff)
            
            transit_callback_index = routing.RegisterTransitCallback(vehicle_cost_callback)
            routing.SetArcCostEvaluatorOfVehicle(transit_callback_index, v_idx)
            fixed_cost = vehicle_data.get('fixed_cost', 0)
            routing.SetFixedCostOfVehicle(fixed_cost, v_idx)

        # --- 4. 维度约束 ---
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

        # 时间维度
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            travel = get_time_min(from_node, manager.IndexToNode(to_index))
            service = 0
            if from_node != 0:
                service = DEFAULT_SERVICE_TIME
            return travel + service

        time_cb_idx = routing.RegisterTransitCallback(time_callback)
        routing.AddDimension(
            time_cb_idx,
            24 * 60 * 7, 
            24 * 60 * 10, # 稍微放宽最大行程以便观察
            False, "Time"
        )
        time_dim = routing.GetDimensionOrDie("Time")

        # --- 5. 业务约束实现 ---
        dist_dim = routing.GetDimensionOrDie('Weight')
        
        for i in range(len(shipments)):
            p_index = manager.NodeToIndex(pickup_indices[i])
            d_index = manager.NodeToIndex(delivery_indices[i])
            
            routing.AddPickupAndDelivery(p_index, d_index)
            routing.solver().Add(routing.VehicleVar(p_index) == routing.VehicleVar(d_index))
            routing.solver().Add(dist_dim.CumulVar(p_index) <= dist_dim.CumulVar(d_index))

            # [新增] 就绪时间 (Ready Time / Earliest Start Time)
            # 车辆必须在 ready_min 之后才能进行 Pickup
            ready_min = shipments[i].get('ready_min', 0)
            if ready_min > 0:
                time_dim.CumulVar(p_index).SetMin(ready_min)

            # 软时间窗 (Deadline)
            deadline = shipments[i].get('deadline_min')
            penalty = shipments[i].get('penalty', 100)
            if deadline is not None and deadline > 0:
                time_dim.SetCumulVarSoftUpperBound(d_index, deadline, penalty)

        routing.SetPickupAndDeliveryPolicyOfAllVehicles(pywrapcp.RoutingModel.PICKUP_AND_DELIVERY_LIFO)

        # 技能匹配
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
            if compatible:
                routing.VehicleVar(p_index).SetValues(compatible)
                routing.VehicleVar(d_index).SetValues(compatible)

        # --- 6. 求解 ---
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
        search_parameters.time_limit.seconds = 5

        print(f"   [算法核心] 启动计算 (车辆数:{len(vehicles)}, 订单数:{len(shipments)})...")
        solution = routing.SolveWithParameters(search_parameters)

        if not solution:
            print("⚠️ 算法未找到可行解！")
            return {"routes": []}

        return extract_solution(manager, routing, solution, vehicles, locations, shipments, time_dim)

def extract_solution(manager, routing, solution, vehicles, locations, shipments, time_dim):
    routes_json = []
    weight_dim = routing.GetDimensionOrDie("Weight")
    
    for vehicle_id in range(len(vehicles)):
        index = routing.Start(vehicle_id)
        if routing.IsEnd(solution.Value(routing.NextVar(index))):
            continue 
            
        steps = []
        
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            time_val = solution.Value(time_dim.CumulVar(index))
            load_w = solution.Value(weight_dim.CumulVar(index))
            
            step_type = "start"
            oid = "-"
            ready_msg = ""
            
            if node_index != 0:
                s_idx = (node_index - 1) // 2
                is_pickup = (node_index - 1) % 2 == 0
                step_type = "pickup" if is_pickup else "delivery"
                oid = shipments[s_idx]['id']
                
                # 如果是装货点，显示该订单的就绪时间
                if is_pickup:
                    r_time = shipments[s_idx].get('ready_min', 0)
                    if r_time > 0:
                        r_hour = r_time // 60
                        ready_msg = f"(订单于 {r_hour}h 生成)"

            day = time_val // (24 * 60)
            hour = (time_val % (24 * 60)) // 60
            minute = time_val % 60
            time_str = f"D{day+1} {hour:02d}:{minute:02d}"

            # 组合展示字符串
            extra_info = oid
            if ready_msg:
                extra_info = f"#{oid} {ready_msg}"
            elif oid != "-":
                extra_info = f"#{oid}"

            steps.append({
                "type": step_type,
                "location": locations[node_index],
                "load": [load_w, 0],
                "arrival": time_str,
                "order_id": extra_info
            })
            
            index = solution.Value(routing.NextVar(index))
        
        steps.append({"type": "end", "location": locations[0], "load": [0,0], "arrival": "End", "order_id": "-"})
        routes_json.append({"vehicle": vehicles[vehicle_id]['id'], "steps": steps})
        
    return {"routes": routes_json}