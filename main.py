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

def run_demo():
    print(">>> 1. 系统初始化 (模块化版)...")
    builder = VroomInputBuilder()

    # --- 1. 读取车辆文件 ---
    try:
        if not os.path.exists(VEHICLE_FILE):
            print(f"❌ 错误: 找不到文件 {VEHICLE_FILE}。请确保已创建 'data' 文件夹并将 csv 放入其中。")
            return

        df_vehicles = pd.read_csv(VEHICLE_FILE)
        print(f"   正在加载车辆... (共 {len(df_vehicles)} 行)")
        
        for index, row in df_vehicles.iterrows():
            skills = clean_skills(row.get('skills', ''))
            
            vehicle = TrunkVehicle(
                id=int(row['id']),
                start_location=[float(row['start_x']), float(row['start_y'])],
                end_location=[float(row['start_x']), float(row['start_y'])],
                capacity=Dimensions(int(row['cap_weight']), int(row['cap_volume'])),
                skills=skills
            )
            builder.add_vehicle(vehicle)
            
    except Exception as e:
        print(f"❌ 车辆文件读取失败: {e}")
        return

    # --- 2. 读取订单文件 ---
    try:
        if not os.path.exists(ORDER_FILE):
            print(f"❌ 错误: 找不到文件 {ORDER_FILE}")
            return

        df_orders = pd.read_csv(ORDER_FILE)
        print(f"   正在加载订单... (共 {len(df_orders)} 行)")
        
        for index, row in df_orders.iterrows():
            skills_req = clean_skills(row.get('skill_req', ''))
            
            order = TrunkOrder(
                id=int(row['id']),
                pickup_location=[float(row['pick_x']), float(row['pick_y'])],
                delivery_location=[float(row['del_x']), float(row['del_y'])],
                amount=Dimensions(int(row['weight']), int(row['volume'])),
                required_skills=skills_req
            )
            builder.add_order(order)
            
    except Exception as e:
        print(f"❌ 订单文件读取失败: {e}")
        return

    # --- 3. 生成数据并【自检】 ---
    input_json = builder.build()
    
    print("\n========= [数据自检] =========")
    if input_json['vehicles']:
        v1 = input_json['vehicles'][0]
        print(f"🔍 车辆样本 (ID {v1['id']}): 技能={v1['skills']} (类型: {type(v1['skills'])})")
    
    print("==============================\n")

    # --- 4. 调用算法 ---
    print(f">>> 2. 数据检查完毕。启动计算...")
    real_result = OrToolsSolver.solve(input_json)
    
    # 解析输出
    PlanParser.parse(real_result)

if __name__ == "__main__":
    run_demo()