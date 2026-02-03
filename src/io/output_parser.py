class PlanParser:
    @staticmethod
    def parse(result_json):
        if not result_json.get('routes'):
            print("\n============================================================")
            print("⚠️ 暂无调度方案 (可能因约束冲突或无解)")
            print("============================================================")
            return

        print("\n======================================================================================================")
        print("🚛 干线运输计划表 (站点聚合版)")
        print("======================================================================================================")
        print("说明: 同一站点的多个装卸动作已合并，时间包含了一次性靠台作业时间。")

        type_map = {
            "start": "始发",
            "end": "回场",
            "pickup": "装",
            "delivery": "卸"
        }

        for route in result_json['routes']:
            vid = route['vehicle']
            
            print(f"\n[车辆 {vid}] 路线详情:")
            print("-" * 150)
            # 调整列宽，增加体积显示
            print(f"{'到达时间':<16} | {'站点类型':<6} | {'地点坐标':<20} | {'当前载重 (kg)':<18} | {'当前容量 (m³)':<18} | {'作业内容 (订单ID)'}")
            print("-" * 150)

            # --- 聚合逻辑 ---
            raw_steps = route['steps']
            if not raw_steps:
                continue

            merged_stops = []
            current_stop = None

            for step in raw_steps:
                loc_key = str(step['location']) 
                step_type = step['type']
                oid = step['order_id']
                
                # [修复] 读取重量和体积
                curr_w = step['load'][0]
                curr_v = step['load'][1]

                if current_stop is None or loc_key != current_stop['loc_key'] or step_type == 'end':
                    
                    if current_stop:
                        merged_stops.append(current_stop)
                    
                    current_stop = {
                        'loc_key': loc_key,
                        'arrival': step['arrival'],
                        'types': set(),
                        'location_display': str(step['location']),
                        # [修复] 初始显示包含重量和体积
                        'load_display': f"{curr_w}kg / {curr_v}m³",
                        'actions': []
                    }
                    if step_type not in ['start', 'end']:
                        current_stop['types'].add("途经")
                    elif step_type == 'start':
                        current_stop['types'].add("始发")
                    elif step_type == 'end':
                        current_stop['types'].add("回场")

                # --- 在当前站点累加动作 ---
                if oid != '-':
                    action_str = f"{type_map.get(step_type, step_type)}#{oid}"
                    current_stop['actions'].append(action_str)
                
                # [修复] 更新最新的载重状态 (重量/体积)
                current_stop['load_weight_display'] = f"{curr_w}kg"
                current_stop['load_volume_display'] = f"{curr_v}m³"

            if current_stop:
                merged_stops.append(current_stop)

            # --- 打印输出 ---
            for stop in merged_stops:
                time_str = stop['arrival']
                
                type_display = "站点"
                if "始发" in stop['types']: type_display = "始发"
                elif "回场" in stop['types']: type_display = "回场"
                
                loc_str = stop['location_display']
                weight_str = stop['load_weight_display']
                volume_str = stop['load_volume_display']

                if stop['actions']:
                    action_msg = ", ".join(stop['actions'])
                else:
                    action_msg = "-"

                print(f"{time_str:<20} | {type_display:<8} | {loc_str:<24} | {weight_str:<22} | {volume_str:<22} | {action_msg}")

            print("-" * 150)