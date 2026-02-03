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
    
    cost_per_km: float = 1.0       
    fixed_cost: int = 0            
    max_distance_km: int = 3000    

@dataclass
class TrunkOrder:
    """干线订单模型 (M2 时间窗增强版)"""
    id: int
    pickup_location: List[float]
    delivery_location: List[float]
    amount: Dimensions
    required_skills: List[str] = field(default_factory=list)
    
    # --- 时间窗核心参数 ---
    # ready_time_min: 订单生成时间/货物就绪时间 (最早什么时候能去提货)
    # delivery_deadline_min: 最晚送达时间
    ready_time_min: int = 0 
    delivery_deadline_min: Optional[int] = None 
    
    penalty_per_min: int = 10