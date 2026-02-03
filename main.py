import os
import pandas as pd
from datetime import datetime

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

# --- [配置] 只匹配日期格式 ---
DATE_FMT = "%Y-%m-%d"

def parse_date_simple(date_str, is_end_of_day=False):
    """
    简易日期解析器:
    将 '2026-02-03' 转换为 datetime 对象。
    is_end_of_day=True  -> 变成 2026-02-03 23:59:59 (截止时间)
    is_end_of_day=False -> 变成 2026-02-03 00:00:00 (就绪时间)
    """
    if pd.isna(date_str) or str(date_str).strip() == "":
        return None
    try:
        s = str(date_str).strip()
        dt = datetime.strptime(s, DATE_FMT)
        
        if is_end_of_day:
            return dt.replace(hour=23, minute=59, second=59)
        else:
            return dt.replace(hour=0, minute=0, second=0)
    except ValueError:
        print(f"⚠️ 日期格式警告: '{date_str}' 无法解析，请使用 YYYY-MM-DD")
        return None

def run_trunk_opt():
    print(">>> 🚚 启动干线物流调度 (M4 日期简化版)...")
    builder = VroomInputBuilder()

    # --- 1. 读取车辆 ---
    try:
        if not os.path.exists(VEHICLE_FILE):
            print(f"❌ 错误: 找不到文件 {VEHICLE_FILE}")
            return

        df_vehicles = pd.read_csv(VEHICLE_FILE)
        print(f"   正在加载车辆... (共 {len(df_vehicles)} 辆)")
        
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

    # --- 2. 读取订单 & 处理日期 ---
    try:
        if not os.path.exists(ORDER_FILE):
            print(f"❌ 错误: 找不到文件 {ORDER_FILE}")
            return

        df_orders = pd.read_csv(ORDER_FILE)
        print(f"   正在加载订单... (共 {len(df_orders)} 单)")
        
        # 2.1 批量处理日期列
        # ready_time -> 当天 00:00
        df_orders['ready_dt'] = df_orders['ready_time'].apply(lambda x: parse_date_simple(x, is_end_of_day=False))
        # deadline_time -> 当天 23:59
        df_orders['deadline_dt'] = df_orders['deadline_time'].apply(lambda x: parse_date_simple(x, is_end_of_day=True))

        # 2.2 确定基准时间 (T=0)
        # 找到最早的一个 ready_dt 作为整个模拟的起点
        valid_starts = df_orders['ready_dt'].dropna()
        if valid_starts.empty:
            sim_start_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        else:
            sim_start_time = valid_starts.min()
            
        print(f"   📅 模拟基准日期 (T=0): {sim_start_time.strftime('%Y-%m-%d')}")

        for index, row in df_orders.iterrows():
            skills_req = clean_skills(row.get('skill_req', ''))
            
            # 计算相对于基准时间的分钟数
            ready_min = 0
            if pd.notna(row['ready_dt']):
                delta = row['ready_dt'] - sim_start_time
                ready_min = int(delta.total_seconds() / 60)
                ready_min = max(0, ready_min)

            deadline_min = None
            if pd.notna(row['deadline_dt']):
                delta = row['deadline_dt'] - sim_start_time
                deadline_min = int(delta.total_seconds() / 60)

            order = TrunkOrder(
                id=int(row['id']),
                pickup_location=[float(row['pick_x']), float(row['pick_y'])],
                delivery_location=[float(row['del_x']), float(row['del_y'])],
                amount=Dimensions(int(row['weight']), int(row['volume'])),
                required_skills=skills_req,
                delivery_deadline_min=deadline_min,
                ready_time_min=ready_min
            )
            builder.add_order(order)
            
    except Exception as e:
        print(f"❌ 订单文件读取失败: {e}")
        return

    # --- 3. 求解与输出 ---
    input_json = builder.build()
    
    print("\n========= [调度计算] =========")
    print("目标: 最小化总成本 (里程费 + 固定费 + 延误惩罚)")
    
    # 将基准时间传递给 Solver，用于结果展示时还原回真实时间
    result = OrToolsSolver.solve(input_json, start_time=sim_start_time)
    
    # 解析输出
    PlanParser.parse(result)

if __name__ == "__main__":
    run_trunk_opt()