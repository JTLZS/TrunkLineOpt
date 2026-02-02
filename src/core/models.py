from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class Dimensions:
    """定义多维容量：[重量kg, 体积m3]"""
    weight: int
    volume: int

    def to_array(self) -> List[int]:
        return [self.weight, self.volume]

@dataclass
class TrunkVehicle:
    """干线车辆模型 (增强版)"""
    id: int
    start_location: List[float]
    end_location: List[float]
    capacity: Dimensions
    skills: List[str] = field(default_factory=list)
    
    # --- 干线新增属性 ---
    cost_per_km: float = 1.0       # 每公里运输成本 (大车更贵)
    fixed_cost: int = 0            # 发车固定成本 (过路费/司机底薪)
    max_distance_km: int = 3000    # 最大行驶里程限制 (防止疲劳驾驶)

@dataclass
class TrunkOrder:
    """干线订单模型 (增强版)"""
    id: int
    pickup_location: List[float]
    delivery_location: List[float]
    amount: Dimensions
    required_skills: List[str] = field(default_factory=list)
    
    # --- 干线新增属性 ---
    # 软时间窗：期望在多少小时内送达。如果超时，会有惩罚成本，但不会无解。
    # 单位：分钟 (从 0时刻 开始计算)
    delivery_deadline_min: Optional[int] = None 
    penalty_per_min: int = 10  # 超时每分钟的惩罚系数