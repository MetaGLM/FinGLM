---
license: Apache License 2.0
source_datasets:
- original 
tags:
- ChatGLM
- Fintech

---

### News
- 新增pdf转txt后的数据，参考下文”txt数据下载“章节  (0728)
- 【重要】datasets包最新版本有兼容性问题，需要安装2.8.0版本，执行：pip3 install datasets==2.8.0  (0725)
- 【重要】新增支持git clone方式下载数据  (0722)
- 【重要】请将modelscope sdk升级到v1.7.2rc0，执行： pip3 install "modelscope==1.7.2rc0" -f https://modelscope.oss-cn-beijing.aliyuncs.com/releases/repo.html    (0722)
- 文件名加载后路径中会显示出sha码，在数据集增加了新字段，'name'-便于显示文件名，参考”数据集加载方式-备注-2“    (0721)
- 补充数据：数据已经从9493条补充到11588，使用sdk加载，参考”数据集加载方式-备注-2“    (0721)
- 新增load数据集自定义cache路径提示，参考”数据集加载方式“  (0721)
- 新增提交示例和测试问题两个文件  (0720)
- 增加数据描述  (0720)


### 背景
在金融领域，构建一个能够像专家一样解读上市公司年报对话交互的智能系统一直是人工智能发展的重要目标。尽管当前的AI系统在文本对话上已经取得了显著的进步，但在更细粒度、更具挑战性的金融场景交互上，其性能仍有待提高。因此，我们寻求在现有大模型的基础上进行能力增强，通过微调大模型、大小模型协同、向量数据库等先进的方法，以期提升AI模型的性能。

为推动此项工作，智谱AI、安硕信息、ModelScope社区、阿里天池竞赛平台、以及北京交通大学联合组织了一场特殊的竞赛。

在竞赛中，我们将使用从上海证券交易所和深圳证券交易所收集的2019-2021年期间部分上市公司的年报作为数据源。上市公司年报是一份能全面揭示公司经营状况、财务状况以及未来发展规划的重要文件。年报内容丰富，包括但不限于公司的组织架构、员工结构、业务进展、财务数据、战略规划等信息。同时，年报还包含对外部市场环境、行业发展趋势、公司的竞争地位的深度分析，为投资者和其他利益相关者提供了重要的参考信息。

然而，解读年报并非易事。年报通常包含大量的专业金融和商业术语，甚至一些暗含的信息，如潜在的风险或利好。这就需要我们以专业知识和深入的理解能力，提取其中的有价值信息。
我们的目标就是利用上市公司年报的内容，构建和训练AI模型，使其具备解读年报、进行深度金融分析的能力，如同一个真正的专家。这将涉及到微调数据集、构建向量库等步骤，以及大模型的训练和微调等技术手段。我们期待这场竞赛能激发出更多的创新思维和技术突破，推动金融领域人工智能的进一步发展。


### 数据集描述
我们在ModelScope社区上传了2019年至2021年期间的部分上市公司年度报告数据集，该数据集包含了11588个详尽的PDF文件。您可以利用这些PDF文件的内容来构建您需要的数据库或者向量库。

以下是我们推荐的处理步骤：

1、PDF文本和表格提取：您可以使用如pdfplumber、pdfminer等工具包提取PDF文件中的文本和表格数据。

2、数据切分：根据PDF文件的目录、子目录和章节信息，对内容进行精确的切块处理。

3、构建基础金融数据库：依据金融知识和PDF内容，设计专业的金融数据库字段和格式。例如，定义资产负债表、现金流量表和利润表等。

4、信息提取：使用大模型的信息提取能力和NLP技术来抽取对应的金融字段信息。例如，请使用json方式输出目录的内容，其中章节的名称作为key，页码作为value。同时，请详细地抽取表格内的数据，以JSON格式输出。

5、构建金融知识问答库：结合构建的金融数据库，应用大模型构建基础的金融问答库。例如，
```
    {"question"："某公司2021年的财务费用为多少元？", "answer": "某公司2021年的财务费用为XXXX元。"}
    prompt:用多种句式修改question及answer的内容。

    {"question":"为什么财务费用可以是负的？", "answer": ""}
    prompt：请模仿上面的question给出100个类似的问题与对应的答案，用json输出。
 ```
 
6、构建向量库：借助于如Word2Vec、Text2Vec等技术，从原始文本数据中提取出语义向量。使用pgvector这种基于PostgreSQL的扩展来存储和索引这些向量，从而建立起一个可供高效查询的大规模向量库。

7、应用：结合向量库、大模型、langchain等工具，提升应用效果。


#### 训练集
- 大小：69GB
- 文件格式：pdf文件
- 文件数量：11588
- 加载方式： sdk加载

#### 提交示例
- 文件名：submit_example.json
- 加载方式：页面下载，参考”数据集文件“tab页

#### 测试问题
- 文件名：test_questions.json
- 加载方式：页面下载，参考”数据集文件“tab页



### 数据集加载方式
#### git加载
```python
# 要求安装 git lfs
git clone http://www.modelscope.cn/datasets/modelscope/chatglm_llm_fintech_raw_dataset.git
```

#### sdk加载
```python
# Note: 
# 1. 【重要】请将modelscope sdk升级到v1.7.2rc0，执行： pip3 install "modelscope==1.7.2rc0" -f https://modelscope.oss-cn-beijing.aliyuncs.com/releases/repo.html
# 2. 【重要】datasets版本限制为 >=2.8.0, <=2.13.0，可执行： pip3 install datasets==2.13.0

from modelscope.msdatasets import MsDataset

# 使用流式方式加载「推荐」
# 无需全量加载到cache，随下随处理
# 其中，通过设置 stream_batch_size 可以使用batch的方式加载

ds = MsDataset.load('chatglm_llm_fintech_raw_dataset', split='train', use_streaming=True, stream_batch_size=1)
for item in ds:
    print(item)

# 加载结果示例（单条，pdf:FILE字段值为该pdf文件本地缓存路径，文件名做了SHA转码，可以直接打开） 
{'name': ['2020-03-24__北京鼎汉技术集团股份有限公司__300011__鼎汉技术__2019年__年度报告.pdf'], 'pdf:FILE': ['~/.cache/modelscope/hub/datasets/modelscope/chatglm_llm_fintech_raw_dataset/master/data_files/430da7c46fb80d4d095a57b4fb223258ffa1afe8bf53d0484e3f2650f5904b5c']}


# 备注: 
1. 自定义缓存路径，可以自行设置cache_dir参数，即 MsDataset.load(..., cache_dir='/to/your/path')
2. 补充数据加载（从9493条增加到11588条），sdk加载注意事项
    a) 删除缓存中的csv映射文件(默认路径为)： ~/.cache/modelscope/hub/datasets/modelscope/chatglm_llm_fintech_raw_dataset/master/data_files/732dc4f3b18fc52380371636931af4c8
    b) 使用MsDataset.load(...) 加载，默认会reuse已下载过的文件，不会重复下载。


```

#### txt数据下载
```python
# Note: pdf转txt格式文件，方便大家复用（有个文件损坏了，所以总数比pdf少1个，共11587 个）

# Linux
wget https://sail-moe.oss-cn-hangzhou.aliyuncs.com/open_data/hackathon_chatglm_fintech/alltxt.zip

# Windows示例
Invoke-WebRequest -Uri https://sail-moe.oss-cn-hangzhou.aliyuncs.com/open_data/hackathon_chatglm_fintech/alltxt.zip -OutFile D:\\alltxt.zip
```



## 数据集版权信息
数据集已经开源，license为Apache License 2.0，如有违反相关条款，随时联系modelscope删除。
