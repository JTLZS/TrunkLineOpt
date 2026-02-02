import math
from typing import List, Dict

class RoutingEngine:
    @staticmethod
    def calculate_distance(loc1, loc2):
        """
        简单计算两点距离 (模拟)
        loc1, loc2: [经度, 纬度]
        返回: 距离 (单位: km)
        """
        dx = loc1[0] - loc2[0]
        dy = loc1[1] - loc2[1]
        # 假设 1度 ≈ 111km (简易估算)
        return math.hypot(dx, dy) * 111

    # 未来可以在这里扩展:
    # @staticmethod
    # def get_distance_matrix(locations):
    #     ... 调用外部 API 获取真实路网距离 ...