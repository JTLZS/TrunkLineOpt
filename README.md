TrunkLineOpt/
├── data/                   # [新建] 存放 CSV 数据文件
│   ├── vehicles.csv
│   └── orders.csv
├── src/                    # [新建] 源代码根目录
│   ├── core/               # 领域模型
│   │   ├── __init__.py
│   │   └── models.py
│   ├── io/                 # 输入输出处理
│   │   ├── __init__.py
│   │   ├── input_builder.py
│   │   └── output_parser.py
│   ├── services/           # 核心业务逻辑/算法
│   │   ├── __init__.py
│   │   ├── solver_service.py
│   │   └── matrix_service.py
│   └── utils/              # 通用工具
│       ├── __init__.py
│       └── helpers.py      # [新建] 提取出的工具函数
├── main.py                 # 程序入口 (代码量大幅减少，只负责调度)
├── requirements.txt
└── .gitignore