import os
import pandas as pd

# 引入模块化后的类和函数
from src.core.models import TrunkVehicle, TrunkOrder, Dimensions
from src.io.input_builder import VroomInputBuilder
from src.io.output_parser import PlanParser
from src.services.solver_service import OrToolsSolver
from src.utils.helpers import clean_skills

# 定义数据文件路径
DATA_DIR = 'data'
VEHICLE_FILE = os.path.join(DATA_DIR, 'vehicles.csv')
ORDER_FILE = os.path.join(DATA_DIR, 'orders.csv')

def run_trunk_opt():
    print(">>> 🚚 启动干线物流智能调度引擎 (M2 时间窗增强版)...")
    builder = VroomInputBuilder()

    # --- 1. 读取车辆文件 ---
    try:
        if not os.path.exists(VEHICLE_FILE):
            print(f"❌ 错误: 找不到文件 {VEHICLE_FILE}")
            return

        df_vehicles = pd.read_csv(VEHICLE_FILE)
        print(f"   正在加载车辆... (共 {len(df_vehicles)} 行)")
        
        for index, row in df_vehicles.iterrows():
            skills = clean_skills(row.get('skills', ''))
            cost_km = float(row.get('cost_km', 1.5))       
            fixed_cost = int(row.get('fixed_cost', 200))   

            vehicle = TrunkVehicle(
                id=int(row['id']),
                start_location=[float(row['start_x']), float(row['start_y'])],
                end_location=[float(row['start_x']), float(row['start_y'])],
                capacity=Dimensions(int(row['cap_weight']), int(row['cap_volume'])),
                skills=skills,
                cost_per_km=cost_km,
                fixed_cost=fixed_cost
            )
            builder.add_vehicle(vehicle)
            
    except Exception as e:
        print(f"❌ 车辆文件读取失败: {e}")
        return

    # --- 2. 读取订单文件 (新增 ready_hour) ---
    try:
        if not os.path.exists(ORDER_FILE):
            print(f"❌ 错误: 找不到文件 {ORDER_FILE}")
            return

        df_orders = pd.read_csv(ORDER_FILE)
        print(f"   正在加载订单... (共 {len(df_orders)} 行)")
        
        for index, row in df_orders.iterrows():
            skills_req = clean_skills(row.get('skill_req', ''))
            
            # 读取截止时间
            deadline_hour = row.get('deadline_hour', None)
            deadline_min = int(deadline_hour * 60) if pd.notna(deadline_hour) else None

            # [新增] 读取下单时间/就绪时间
            ready_hour = row.get('ready_hour', 0) # 默认为0，即立刻可取
            ready_min = int(ready_hour * 60)

            order = TrunkOrder(
                id=int(row['id']),
                pickup_location=[float(row['pick_x']), float(row['pick_y'])],
                delivery_location=[float(row['del_x']), float(row['del_y'])],
                amount=Dimensions(int(row['weight']), int(row['volume'])),
                required_skills=skills_req,
                delivery_deadline_min=deadline_min,
                ready_time_min=ready_min # 传入模型
            )
            builder.add_order(order)
            
    except Exception as e:
        print(f"❌ 订单文件读取失败: {e}")
        return

    # --- 3. 求解与输出 ---
    input_json = builder.build()
    
    print("\n========= [调度计算] =========")
    print("目标: 最小化总成本 (里程费 + 固定费 + 延误惩罚)")
    result = OrToolsSolver.solve(input_json)
    
    # 解析输出
    PlanParser.parse(result)

if __name__ == "__main__":
    run_trunk_opt()