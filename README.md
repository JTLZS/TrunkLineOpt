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
| **当前版本** | `v4.0` (站点聚合、固定靠台时长、软时间窗) |
| **核心算法** | Routing Model / Guided Local Search (GLS) |
| **关键特性** | **站点级聚合展示**、**固定作业时长**、多维装载、技能匹配、LIFO 堆叠、异构车队成本 |
| **最后更新** | 2026-02-03 |

---

## ✨ 版本特性（Features)

本项目针对干线/城配（Milk Run）场景，从“订单维度”升级为**“站点维度”**。系统现在能自动识别同一地点的连续作业，合并装卸动作，并采用“固定靠台时间”计算逻辑，完美模拟大车“一站装多单”的实际运营模式。：

* 🏭 **站点级作业聚合 (Site-Level Aggregation)**
    传统的 VRP 算法通常按订单处理，导致在同一地点装 5 单货会显示 5 行记录。
    * **智能合并**：本系统自动检测连续的同坐标任务，将其合并为一个“站点节点”。

    * **清晰展示**：输出结果不再冗长，直接显示：“到达北京分拨中心 -> 装：订单#1, #2, #5”。

* ⏱️ ** 固定靠台作业时间 (Fixed Operation Time)**
    干线物流中，时间的消耗主要在于“靠台、排队、解封、办手续”，而非单纯搬运每一个包裹。
    * **逻辑变更**：不再每装一单增加一次时间。

    * **新规则**：
        * 同站作业：同一站点内连续装卸多单，不增加额外时间。
        * 切换站点：车辆移动到新站点时，自动增加一次固定作业时长（代码默认 60分钟），模拟靠台和手续时间。

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
| deadline_time | **(新) 货物送达日期** | 2026-02-04 |
| ready_time | **(新) 货物就绪日期** | 2026-02-02 |

## 3.运行程序
```Bash
python main.py
```
## 4. 查看结果
程序将在终端输出详细的调度计划表，包含：

✅ 任务队列: 每辆车的装载信息。

⏰ 时间估算: 到达每个站点的时间。

📊 装载统计: 实时装载货量。

📝 智能备注: 调度逻辑说明（如：作业内容）。