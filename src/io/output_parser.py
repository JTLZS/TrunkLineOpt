class PlanParser:
    @staticmethod
    def parse(result_json):
        if not result_json.get('routes'):
            print("\n============================================================")
            print("⚠️ 暂无调度方案 (可能因约束冲突或无解)")
            print("============================================================")
            return

        print("\n=========================================================================================")
        print("🚛 干线运输计划表 (日期简化版)")
        print("=========================================================================================")
        print("说明: 输入为年月日，系统自动规划具体的到达时刻 (起运日00:00 - 截止日23:59)")

        type_map = {
            "start": "出发",
            "end": "回场",
            "pickup": "装货",
            "delivery": "卸货"
        }

        for route in result_json['routes']:
            vid = route['vehicle']
            
            print(f"\n[车辆 {vid}] 任务详情:")
            print("-" * 105)
            # 列宽适配 '02-03 14:30'
            print(f"{'预计到达时间':<18} | {'类型':<6} | {'地点坐标':<20} | {'装载量(kg/方)':<15} | {'订单ID'}")
            print("-" * 105)

            for step in route['steps']:
                t_time = step.get('arrival', '-')
                t_str = type_map.get(step['type'], step['type'])
                loc_str = str(step['location'])
                load_str = f"{step['load'][0]}/{step['load'][1]}"
                
                oid_str = str(step.get('order_id', '-'))
                if oid_str == '-':
                    oid_str = ''

                print(f"{t_time:<18} | {t_str:<6} | {loc_str:<20} | {load_str:<15} | {oid_str}")

            print("-" * 105)