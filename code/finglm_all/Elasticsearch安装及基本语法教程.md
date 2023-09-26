# Elasticsearch 安装、基本语法及Python客户端教程

- [安装](#安装)
  - [Elasticsearch 安装](#elasticsearch-安装)
  - [启动Elasticsearch](#启动elasticsearch)
- [基本语法](#基本语法)
  - [创建索引](#创建索引)
  - [索引文档](#索引文档)
  - [基本检索](#基本检索)
  - [复杂检索示例](#复杂检索示例)
  - [更新和删除文档](#更新和删除文档)
  - [删除索引](#删除索引)
- [使用Python Elasticsearch客户端](#使用python-elasticsearch客户端)
  - [安装](#安装-1)
  - [连接到Elasticsearch](#连接到elasticsearch)
  - [基本操作](#基本操作)
  
## 安装

### Elasticsearch 安装

首先，确保您的系统已安装Java 8或更高版本，因为Elasticsearch需要Java运行环境。

#### Windows

1. 从 [Elasticsearch官网](https://www.elastic.co/start) 下载适合Windows的ZIP包。
2. 解压ZIP文件。
3. 运行 `bin\elasticsearch.bat`。

#### macOS (使用Homebrew)

```bash
brew tap elastic/tap
brew install elastic/tap/elasticsearch-full
```

#### Ubuntu

```bash
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch | sudo apt-key add -
sudo apt-get install apt-transport-https
sudo sh -c 'echo "deb https://artifacts.elastic.co/packages/7.x/apt stable main" > /etc/apt/sources.list.d/elastic-7.x.list'
sudo apt-get update && sudo apt-get install elasticsearch
```

### 启动Elasticsearch

#### Windows

```bash
bin\elasticsearch
```

#### macOS 和 Ubuntu

```bash
sudo service elasticsearch start
```

## 基本语法

Elasticsearch主要使用RESTful API，您可以使用如`curl`的工具进行交互。

### 创建索引

```bash
curl -X PUT "localhost:9200/my_index"
```

### 索引文档

```bash
curl -X POST "localhost:9200/my_index/_doc/" -H 'Content-Type: application/json' -d'
{
    "name": "John Doe",
    "age": 30
}'
```

### 基本检索

1. **使用URI搜索**:

   ```bash
   curl -X GET "localhost:9200/my_index/_search?q=name:John"
   ```

2. **使用请求体搜索**:

   ```bash
   curl -X GET "localhost:9200/my_index/_search" -H 'Content-Type: application/json' -d'
   {
       "query": {
           "match": {
               "name": "John"
           }
       }
   }'
   ```

### 复杂检索示例

1. **组合查询**:

   ```bash
   curl -X GET "localhost:9200/my_index/_search" -H 'Content-Type: application/json' -d'
   {
       "query": {
           "bool": {
               "must": [
                   { "match": { "name": "John" } },
                   { "range": { "age": { "gte": 25 } } }
               ]
           }
       }
   }'
   ```

### 更新和删除文档

1. **更新文档**:

   ```bash
   curl -X POST "localhost:9200/my_index/_update/document_id" -H 'Content-Type: application/json' -d'
   {
     "doc": { "age": 31 }
   }'
   ```

2. **删除文档**:

   ```bash
   curl -X DELETE "localhost:9200/my_index/_doc/document_id"
   ```

### 删除索引

```bash
curl -X DELETE "localhost:9200/my_index"
```

## 使用Python Elasticsearch客户端

### 安装

首先，您需要安装Python Elasticsearch客户端库。您可以使用pip进行安装：

```bash
pip install elasticsearch
```

### 连接到Elasticsearch

使用Elasticsearch客户端，首先需要建立连接：

```python
from elasticsearch import Elasticsearch

# 默认连接localhost:9200
es = Elasticsearch()

# 或指定主机和端口
es = Elasticsearch(hosts=["http://your_host:your_port"])
```

### 基本操作

1. **创建索引**:

   ```python
   es.indices.create(index="my_index", ignore=400)
   ```

2. **索引文档**:

   ```python
   doc_data = {
       "name": "John Doe",
       "age": 30
   }
   response = es.index(index="my_index", doc_type="_doc", body=doc_data)
   ```

3. **检索文档**:

   ```python
   response = es.search(index="my_index", body={
       "query": {
           "match": {
               "name": "John"
           }
       }
   })
   ```

4. **更新文档**:

   ```python
   update_data = {
       "doc": { "age": 31 }
   }
   response = es.update(index="my_index", doc_type="_doc", id=document_id, body=update_data)
   ```

5. **删除文档**:

   ```python
   response = es.delete(index="my_index", doc_type="_doc", id=document_id)
   ```

6. **删除索引**:

   ```python
   es.indices.delete(index="my_index", ignore=[400, 404])
   ```

这只是一个入门级的Elasticsearch教程。为了深入了解其功能，请参阅 [Elasticsearch官方文档](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html) 和 [Python客户端官方文档](https://elasticsearch-py.readthedocs.io/en/latest/)。


