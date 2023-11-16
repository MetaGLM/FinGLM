# ChatGLM金融大模型挑战赛: 随便起个名Baseline

## Repo structure:

/data/allpdf: 存储所有的年报pdf文件
注意: 所有的pdf文件需要以类似`2020-01-21__江苏安靠智能输电工程科技股份有限公司__300617__安靠智电__2019年__年度报告.pdf`的方式命名。


/preprocess_data: 存储数据预处理代码

/dev: 在数据库中查询问题的相关字段

/dev/agent: 利用langchain进行计算问题

/src && /scripts: 存储ChatGLM2 Finetune及Inference代码


## Quick Start
```
pip install -r requirements.txt & bash run.sh
```

## Deploy

1. 将年报pdf文件转化为txt储存 (不能保证所有信息都正确转换)
```
python preprocess_data/pdf2txt.py
```
或者
```
wget -P ./data https://sail-moe.oss-cn-hangzhou.aliyuncs.com/open_data/hackathon_chatglm_fintech/alltxt.zip & unzip alltxt.zip

```

此时获取data/lines_txt所有处理好的txt文件

2. 解析每个alltxt中对应的txt文件，获取三大基本表 + 公司信息 + 员工信息
```
python preprocess_data/transfer_file.py
python preprocess_data/extract_report.py
python preprocess_data/txt_aggregate.py
```

获取data/parse_question.json，其中每一个record包含了对应的`Company_name`，`DATE`，`task_key`

3. 建立数据库 (用于统计数据查询)
```
python dev/create_table.py
```

4. 对问题进行正则匹配，获取对应keyword
```
python dev/extract_question.py
```

5. 查询每个问题对应的数据表，添加查询信息到额外的问题字段`prompt`
```
python dev/search.py
```

6. 使用chatglm进行推断
```
bash scripts/eval.sh
```
获得最终输出结果在`output`文件夹中

7. [Optional] verbaliser, post-progress处理
```
python dev/post_process.py
```

## LLM as Agent for Calculating Financial Problems
(此功能仅仅提供一个思路，实际效果并不如使用预定设置问题回答模版)
在使用dev/search.py获得计算题中相关字段后，使用Langchain PALchain解决计算问题
1. 执行Quick start中的1-5步，获得`data/dataset.json`
2. 开启ChatGLM api, 这里设定开放29501端口 : `python dev/agent/api.py` 
3. 对计算问题进行解析: `python dev/agent/agent_parser.py`


因为chatglm把中文问题解析成PAL的能力不强，所以中间使用额外huggingface模型`Helsinki-NLP/opus-mt-zh-en`对输入问题进行翻译。同时可以使用其他LLM api代替chatglm2(换成中文能力更强的OPENAI gpt-turbo3.5可以不使用翻译)。

为了提升中文PAL prompt能力，可以根据需求自行构建`dev/agent/math-prompt.py`的PAL prompt。



## Miscellaneous
预处理阶段，pdf2txt数据提取准确率不足，需要配合更细粒度的数据提取工具。