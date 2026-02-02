from dataclasses import dataclass, field
from typing import List

@dataclass
class Dimensions:
    """定义多维容量：[重量kg, 体积m3] (功能点A)"""
    weight: int
    volume: int

    def to_array(self) -> List[int]:
        return [self.weight, self.volume]

@dataclass
class TrunkVehicle:
    """干线车辆模型"""
    id: int
    start_location: List[float]  # [经度, 纬度]
    end_location: List[float]
    capacity: Dimensions         # 车辆载重限制
    skills: List[str] = field(default_factory=list) # 车辆技能 (功能点B)
    profile: str = "truck"       # 路由模式

@dataclass
class TrunkOrder:
    """干线订单模型"""
    id: int
    pickup_location: List[float]
    delivery_location: List[float]
    amount: Dimensions           # 货物数量
    required_skills: List[str] = field(default_factory=list) # 需求技能 (功能点B)