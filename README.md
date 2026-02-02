# 🚛 TrunkLineOpt - 干线物流智能调度优化引擎

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Solver](https://img.shields.io/badge/Solver-Google%20OR--Tools-DB4437?logo=google&logoColor=white)](https://developers.google.com/optimization)
[![Algorithm](https://img.shields.io/badge/Algorithm-VRP%20with%20LIFO-FF9900)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

> **TrunkLineOpt** 是一个基于 **Google OR-Tools** 求解引擎，结合 **VROOM** 问题建模协议开发的干线物流调度系统。专为解决复杂约束下的车辆路径规划问题（VRP with Pickup and Delivery）而设计。

---

## 📋 项目概览 (Project Overview)

| 属性 | 详细信息 |
| :--- | :--- |
| **当前版本** | `v2.0` (模块化重构版) |
| **核心算法** | Routing Model / Guided Local Search (GLS) |
| **关键特性** | 多维装载、技能匹配、LIFO 堆叠约束 |
| **最后更新** | 2024-05 |

---

## ✨ 核心功能 (Key Features)

本系统不仅仅是路径规划，更深入解决了实际物流场景中的痛点：

* 📦 **多维容量约束 (Multi-Dimensional Capacity)**
    同时考虑 **重量 (Weight)** 和 **体积 (Volume)** 双重限制，有效防止“重货不满方”或“抛货超方”的装载浪费。

* 🔧 **特种运输技能匹配 (Skill Matching)**
    支持定义车辆技能（如 `cold` 冷链、`danger` 危险品）。系统会自动校验订单需求，确保特种订单只由具备相应资质的车辆承运。

* 🔄 **取送货 & LIFO 策略 (P&D with LIFO)**
    * 严格遵循 **Pick-up and Delivery**（先装后卸）逻辑。
    * 强制执行 **LIFO (Last-In, First-Out)** 堆叠约束，保证后装载的货物先卸载，避免干线运输中的“翻仓”问题。

* ⚖️ **智能负载均衡 (Load Balancing)**
    引入全局跨度成本系数，避免出现“一车累死、一车闲死”的情况，自动平衡车队工作时长。

* 🔌 **VROOM 协议兼容**
    数据层采用类 VROOM 的 JSON 结构，便于未来对接 C++ 高性能引擎或标准前端可视化组件。

---

## 📂 项目结构 (Structure)

项目采用 **领域驱动设计 (DDD)** 风格的模块化结构，逻辑清晰，易于扩展。

```text
TrunkLineOpt/
├── 📂 data/                    # 数据源目录
│   ├── 📄 vehicles.csv         # - 车辆资源表 (运力池)
│   └── 📄 orders.csv           # - 订单需求表 (任务池)
├── 📂 src/                     # 核心源代码
│   ├── 📂 core/                # [领域模型] Data Classes
│   │   └── 🐍 models.py        #   - Vehicle, Order, Dimensions 定义
│   ├── 📂 io/                  # [适配接口] 输入输出处理
│   │   ├── 🐍 input_builder.py #   - CSV -> 求解器标准 JSON 转换
│   │   └── 🐍 output_parser.py #   - 解析求解结果并生成智能报表
│   ├── 📂 services/            # [业务服务] 核心算法层
│   │   ├── 🐍 solver_service.py#   - OR-Tools 约束配置与调用
│   │   └── 🐍 matrix_service.py#   - 距离/时间矩阵计算
│   └── 📂 utils/               # [工具库]
│       └── 🐍 helpers.py       #   - 字符串清洗等辅助函数
├── 🚀 main.py                  # 程序启动入口
├── 📋 requirements.txt         # 依赖包列表
└── 📖 README.md                # 项目说明文档

```

# 🛠️ 快速开始 (Usage)

## 1. 环境准备
   确保已安装 Python 3.8 或更高版本。

   ```bash
   # 1. 克隆项目
   git clone [https://github.com/YourUsername/TrunkLineOpt.git](https://github.com/YourUsername/TrunkLineOpt.git)
   cd TrunkLineOpt

   # 2. 安装依赖
   pip install -r requirements.txt
    ```
```
## 2.准备数据

请在 data/ 目录下创建以下两个 CSV 文件（或直接使用示例数据）：

### 🚗 车辆数据 (data/vehicles.csv)

| id | start_x | start_y | cap_weight | cap_volume | skills |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 101 | 113.3 | 23.1 | 30000 | 80 | cold |
| 102 | 113.3 | 23.1 | 35000 | 80 | |

### 📦 订单数据 (data/orders.csv)

| id | pick_x | pick_y | del_x | del_y | weight | volume | skill_req |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 113.3 | 23.1 | 116.4 | 39.9 | 5000 | 10 | cold |
| 2 | 113.3 | 23.1 | 116.4 | 39.9 | 2000 | | |

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

