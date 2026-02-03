class VroomInputBuilder:
    def __init__(self):
        self.vehicles = []
        self.shipments = []

    def add_vehicle(self, vehicle):
        self.vehicles.append(vehicle)

    def add_order(self, order):
        self.shipments.append(order)

    def build(self):
        data = {
            "vehicles": [],
            "shipments": []
        }

        for v in self.vehicles:
            v_dict = {
                "id": v.id,
                "start": v.start_location,
                "end": v.end_location,
                "capacity": [v.capacity.weight, v.capacity.volume],
                "skills": v.skills,
                "cost_per_km": getattr(v, 'cost_per_km', 1.0),
                "fixed_cost": getattr(v, 'fixed_cost', 0)
            }
            data["vehicles"].append(v_dict)

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
                "deadline_min": getattr(o, 'delivery_deadline_min', None),
                "ready_min": getattr(o, 'ready_time_min', 0), # [新增] 传递就绪时间
                "penalty": getattr(o, 'penalty_per_min', 100)
            }
            data["shipments"].append(s_dict)

        return data