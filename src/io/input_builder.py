class VroomInputBuilder:
    def __init__(self):
        self.vehicles = []
        self.shipments = []

    def add_vehicle(self, vehicle):
        self.vehicles.append(vehicle)

    def add_order(self, order):
        self.shipments.append(order)

    def build(self):
        # 构建符合 VROOM/Solver 格式的 JSON
        data = {
            "vehicles": [],
            "shipments": []
        }

        # 1. 转换车辆 (增加成本参数)
        for v in self.vehicles:
            v_dict = {
                "id": v.id,
                "start": v.start_location,
                "end": v.end_location,
                "capacity": [v.capacity.weight, v.capacity.volume],
                "skills": v.skills,
                # 透传 M1 核心成本参数
                "cost_per_km": getattr(v, 'cost_per_km', 1.0),
                "fixed_cost": getattr(v, 'fixed_cost', 0)
            }
            data["vehicles"].append(v_dict)

        # 2. 转换订单 (增加时间窗参数)
        for o in self.shipments:
            s_dict = {
                "id": o.id,
                "pickup": {
                    "location": o.pickup_location
                },
                "delivery": {
                    "location": o.delivery_location
                },
                "amount": [o.amount.weight, o.amount.volume],
                "skills": o.required_skills,
                # 透传 M1 核心时间窗参数
                "deadline_min": getattr(o, 'delivery_deadline_min', None),
                "penalty": getattr(o, 'penalty_per_min', 100)
            }
            data["shipments"].append(s_dict)

        return data