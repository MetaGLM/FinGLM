## 数据/预处理说明

### data文件夹

- data/chatglm_llm_fintech_raw_dataset（官方数据集）

    来源：
    ```
    git clone http://www.modelscope.cn/datasets/modelscope/chatglm_llm_fintech_raw_dataset.git
    ```

- data/alltxt（官方数据集）
    来源：
    ```
    wget https://sail-moe.oss-cn-hangzhou.aliyuncs.com/open_data/hackathon_chatglm_fintech/alltxt.zip
    unzip alltxt.zip
    ```

- data/allhtml（官方提供的baseline提取pdf得到的结果）
    
    来源：
    
    开源baseline提取pdf为html

- data/processed_excels
    
    由process.py 预处理html&txt抽取得到的表格

- data/list_json:

    txt切分成结构化的chunk，用于开放问题检索

- data/final_excels:

    标准化的财务报表、公司信息宽表，用于SQL查询

- finetune/table_qa/data
    
    包含以下几个部分：
    
    1. 规则自动生成的数据集
        1. 公司问答数据，由company_info.py规则生成
        2. 个人问答数据，由personal_information_augmentation.py规则生成
        3. 问题分类数据，由classifier规则生成
    
    然后各自按比例拆分数据集，由chatglm进行ptuning，生成对应的checkpoint
    
    最后得到的模型，输入questions，由classifier.py 推理得出classification.jsonl，用于后续模型回答不同类型的问题参考

    直接运行这几个文件可能会遇到相对路径问题，改一下import路径即可

    微调的脚本位于ChatGLM2-6B/ptuning下面，分别是train_classifier.sh train_personal.sh train_company.sh

- documents/open_questions_annotated:
    规则标注的A榜数据

- documents/open_query:
    CHATGPT为部分开放类型问题生成的答案，作为GLM回答的样例放进prompt里面

- complex_query:
    SQL查询数据生成模板，支持多城市、增长率查询

## 模型说明

模型目录：model/chatglm2-6b
来源：
```
git lfs install
git clone https://huggingface.co/THUDM/chatglm2-6b
```

模型微调代码（CHATGLM2官方repo）: ChatGLM2-6B


checkpoints:
- model/classifier/sql_enhance_checkpoint 问题分类
- model/company_info/checkpoint-1500 公司信息问题回答
- model/personal/checkpoint-1500 员工信息问题回答



## 流程说明

运行 process.py
运行 predict.py
以此法生成的文件位于/tmp/result.json

## 构建并运行docker

sh run_docker.sh
以此法生成的内容保存在result文件夹下
