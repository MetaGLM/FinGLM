---
frameworks:
- Pytorch
license: Apache License 2.0
tasks:
- text-generation
---
###### 该模型当前使用的是默认介绍模版，处于“预发布”阶段，页面仅限所有者可见。
###### 请根据[模型贡献文档说明](https://www.modelscope.cn/docs/%E5%A6%82%E4%BD%95%E6%92%B0%E5%86%99%E5%A5%BD%E7%94%A8%E7%9A%84%E6%A8%A1%E5%9E%8B%E5%8D%A1%E7%89%87)，及时完善模型卡片内容。ModelScope平台将在模型卡片完善后展示。谢谢您的理解。
#### Clone with HTTP
```bash
 git clone https://www.modelscope.cn/nsddd/nsddd_final.git
```

## 模型微调
针对SQL生成的模型微调请参考
[chatglm-sql-fine-tune](./模型finetuning+数据集制作/readme.md)

## 项目推理
#### 文件介绍
```
./submitnsddd/app
├── configs  --->  配置文件目录
│   ├── added_keywords.csv
│   ├── all-pdf-name.txt
│   ├── class3_database.csv
│   ├── __init__.py
│   ├── item_map.csv
│   ├── item_to_parten.csv
│   ├── model_config.py
│   ├── modify.ipynb
│   ├── statistic_query_res.csv
│   └── statistic_query_res_new.csv
├── database  --->  查询数据库构建
│   ├── badcase.ipynb
│   ├── badcase.py
│   ├── fin_data.db
│   ├── gen_csv.py
│   ├── get_null.py
│   ├── __init__.py
│   ├── out.csv
│   ├── __pycache__
│   ├── sql_db.py
│   ├── test_db.py
├── __init__.py
├── log.txt
├── main.py
├── query_sql.py
├── retrieval  --->  向量数据库检索
│   ├── dense_retrieval.py
│   ├── __init__.py
│   ├── __pycache__
│   └── sparse_retrieval.py
├── run.sh
└── utils  --->  辅助程序
    ├── compute_value.py
    ├── find_annual_report.py
    ├── __init__.py
    ├── __pycache__
    ├── query_database.py
    ├── query_map.py
    └── statistic_answer.py
```
#### 推理
docker build -f Dockerfile -t registry.cn-shanghai.aliyuncs.com/chengs18/nsddd:10.0 .

docker run -d -it --gpus all --shm-size=6g -v /data/chengshuang/SMP2023/tcdata:/tcdata --name smp_submit_10.0 registry.cn-shanghai.aliyuncs.com/chengs18/nsddd:10.0
