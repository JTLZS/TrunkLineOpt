# 🚛 TrunkLineOpt - 干线物流智能调度优化引擎（M1增强版）

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Solver](https://img.shields.io/badge/Solver-Google%20OR--Tools-DB4437?logo=google&logoColor=white)](https://developers.google.com/optimization)
[![Algorithm](https://img.shields.io/badge/Algorithm-VRP%20with%20LIFO-FF9900)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

> **TrunkLineOpt** 是一个基于 **Google OR-Tools** 求解引擎，结合 **VROOM** 问题建模协议开发的干线物流调度系统。专为解决复杂约束下的车辆路径规划问题（VRP with Pickup and Delivery）而设计。

---

## 📋 项目概览 (Project Overview)

| 属性 | 详细信息 |
| :--- | :--- |
| **当前版本** | `v3.0` (增加软时间窗、异构车队成本、回程/闭环功能) |
| **核心算法** | Routing Model / Guided Local Search (GLS) |
| **关键特性** | 多维装载、技能匹配、LIFO 堆叠约束、软时间窗、异构车队成本、回程/闭环 |
| **最后更新** | 2026-02-02 |

---

## ✨ 版本特性（Features)

本项目已针对干线物流场景进行了深度定制，实现了以下核心算法能力：

* 💰 **全局成本最优 (Total Cost Minimization)**
    不再单纯追求距离最短，而是追求**财务成本最低**。
    * 异构车队计价： 系统能识别不同车型的成本差异。例如，优先使用每公里成本低的小车处理零散订单，大批量货物则启用大车。

    * 固定启动费： 考虑车辆发车的固定成本（司机底薪、过路费），算法会自动倾向于“减少发车数量”或“满载发车”。

    * 回程配载优化： 自动在回程路线上寻找顺路订单，降低空驶率。

* ⏰ **软时间窗约束 (Soft Time Windows)**
    * 弹性履约： 支持为订单设置“截止时间”（如 48h/72h 到达）。

    * 延误惩罚： 如果因拼单导致稍晚于截止时间，系统不会报错（无解），而是计算延误惩罚成本。算法会自动权衡：是“为了准时而单车专送（高成本）”还是“为了省钱拼单稍微晚点（低成本+惩罚）”。

---

## 📂 项目结构 (Structure)

```text
TrunkLineOpt/
├── 📂 data/                    # 数据源
│   ├── 📄 vehicles.csv         # 运力池 (含成本参数)
│   └── 📄 orders.csv           # 订单池 (含时效参数)
├── 📂 src/                     # 核心源码
│   ├── 📂 core/                # [模型层] 定义 Vehicle, Order, Dimensions
│   ├── 📂 io/                  # [IO层] 输入构建与结果解析
│   ├── 📂 services/            # [服务层]
│   │   └── 🐍 solver_service.py#   ★ 核心算法引擎 (OR-Tools配置)
│   └── 📂 utils/               # [工具层] 辅助函数
├── 🚀 main.py                  # 启动入口
└── 📋 requirements.txt         # 依赖包
```

# 🛠️ 快速开始 (Usage)

## 1. 环境准备
   确保已安装 Python 3.8 或更高版本。

   ```bash
   pip install -r requirements.txt
```
## 2.准备数据

请在 data/ 目录下创建以下两个 CSV 文件。**注意新增加的成本和时间字段**。

### 🚗 车辆数据 (data/vehicles.csv)

| 字段 | 说明 | 示例 |
| :--- | :--- | :--- |
| id | 车辆唯一ID | 101 |
| start_x,start_y | 始发地经纬度 | 113.3, 23.1 |
| cap_weight | 载重上限 (kg) | 30000 |
| cap_volum | 体积上限 (m³) | 80 |
| skills | 车辆技能 | cold |
| cost_km | **(新) 每公里运输成本 (元)** | 3.0 |
| fixed_cost | **(新) 发车固定成本/启动费** | 500 |




### 📦 订单数据 (data/orders.csv)

| 字段 | 说明 | 示例 |
| :--- | :--- | :--- |
| id | 订单ID | 1 |
| pick_x,pick_y | 发货地坐标 | 113.3, 23.1 |
| del_x,del_y | 收货地坐标 | 116.4, 39.9 |
| weight，volum | 货物重量/体积 | 5000，10 |
| skill_req | 需求技能 | cold |
| deadline_hour | **(新) 期望送达时效 (小时)** | 48 |

## 3.运行程序
```Bash
python main.py
```
## 4. 查看结果
程序将在终端输出详细的调度计划表，包含：

✅ 任务队列: 每辆车的详细访问顺序。

⏰ 时间估算: 到达每个站点的时间 (D1 xx:xx)。

📊 装载统计: 实时装载率百分比。

📝 智能备注: 调度逻辑说明（如：为什么这辆车运这个单）。