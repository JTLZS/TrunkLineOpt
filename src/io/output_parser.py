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
            print("-" * 110)
            # 调整列宽
            print(f"{'到达时间':<16} | {'站点类型':<6} | {'地点坐标':<20} | {'当前载重':<10} | {'作业内容 (订单ID)'}")
            print("-" * 110)

            # --- 聚合逻辑 ---
            raw_steps = route['steps']
            if not raw_steps:
                continue

            # 使用列表来存储合并后的站点
            merged_stops = []
            
            current_stop = None

            for step in raw_steps:
                loc_key = str(step['location']) # 用坐标字符串作为唯一标识
                step_type = step['type']
                oid = step['order_id']
                
                # 如果是新的站点，或者 步骤类型是end (防止end和最后一个点混淆)
                if current_stop is None or loc_key != current_stop['loc_key'] or step_type == 'end':
                    
                    # 先保存上一个站点
                    if current_stop:
                        merged_stops.append(current_stop)
                    
                    # 初始化新站点
                    current_stop = {
                        'loc_key': loc_key,
                        'arrival': step['arrival'],
                        'types': set(),
                        'location_display': str(step['location']),
                        'load_display': f"{step['load'][0]}kg",
                        'actions': []  # 存储具体的动作字符串，如 "装#1"
                    }
                    # 如果不是 start/end，记录类型
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
                
                # 更新最新的载重状态 (离开时的状态)
                current_stop['load_display'] = f"{step['load'][0]}kg"

            # 循环结束，添加最后一个站点
            if current_stop:
                merged_stops.append(current_stop)

            # --- 打印输出 ---
            for stop in merged_stops:
                time_str = stop['arrival']
                
                # 决定站点类型显示
                type_display = "站点"
                if "始发" in stop['types']: type_display = "始发"
                elif "回场" in stop['types']: type_display = "回场"
                
                loc_str = stop['location_display']
                load_str = stop['load_display']
                
                # 拼接动作
                if stop['actions']:
                    action_msg = ", ".join(stop['actions'])
                else:
                    action_msg = "-"

                print(f"{time_str:<16} | {type_display:<6} | {loc_str:<20} | {load_str:<10} | {action_msg}")

            print("-" * 110)