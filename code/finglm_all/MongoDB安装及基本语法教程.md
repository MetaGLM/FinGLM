# MongoDB 安装、基本语法及Python客户端教程

- [安装](#安装)
  - [MongoDB 安装](#mongodb-安装)
  - [启动MongoDB](#启动mongodb)
- [基本语法](#基本语法)
  - [创建数据库](#创建数据库)
  - [创建集合](#创建集合)
  - [插入文档](#插入文档)
  - [查询文档](#查询文档)
  - [更新文档](#更新文档)
  - [删除文档](#删除文档)
- [使用Python调用MongoDB](#使用Python调用MongoDB)
  - [安装pymongo](#安装pymongo)
  - [Python代码示例](#Python代码示例)

## 安装

### MongoDB 安装

首先，根据您的操作系统，访问 [MongoDB官方下载页面](https://www.mongodb.com/try/download/community) 以获取相应版本的安装文件。

#### Windows

1. 下载安装包后，双击打开并按照提示完成安装。
2. 为了方便使用，您可以将MongoDB的bin目录添加到系统的`PATH`变量中。

#### macOS (使用Homebrew)

```bash
brew tap mongodb/brew
brew install mongodb-community@5.0
```

#### Ubuntu (以18.04为例)

```bash
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 9DA31620334BD75D9DCB49F368818C72E52529D4
echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu bionic/mongodb-org/5.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-5.0.list
sudo apt-get update
sudo apt-get install -y mongodb-org
```

### 启动MongoDB

#### Windows

```bash
mongod
```

#### macOS 和 Ubuntu

```bash
sudo systemctl start mongod
```

## 基本语法

### 连接到MongoDB

使用`mongo`命令连接到本地MongoDB实例：

```bash
mongo
```

### 基本命令

1. **查看所有数据库**:
   ```javascript
   show dbs
   ```

2. **选择或创建数据库**:
   ```javascript
   use yourDatabaseName
   ```

3. **查看当前数据库中的集合**:
   ```javascript
   show collections
   ```

4. **插入文档**:
   ```javascript
   db.yourCollectionName.insert({name: "John", age: 25})
   ```

5. **查询文档**:
   ```javascript
   db.yourCollectionName.find()
   db.yourCollectionName.find({name: "John"})
   ```

6. **更新文档**:
   ```javascript
   db.yourCollectionName.update({name: "John"}, {$set: {age: 26}})
   ```

7. **删除文档**:
   ```javascript
   db.yourCollectionName.remove({name: "John"})
   ```
   
## 使用Python调用MongoDB

要在Python中连接和操作MongoDB，我们通常使用`pymongo`库。

### 安装pymongo

```bash
pip install pymongo
```

### Python代码示例

```python
from pymongo import MongoClient

# 创建连接
client = MongoClient('localhost', 27017)

# 选择数据库
db = client['yourDatabaseName']

# 选择集合
collection = db['yourCollectionName']

# 插入文档
collection.insert_one({"name": "John", "age": 25})

# 查询文档
for doc in collection.find({"name": "John"}):
    print(doc)

# 更新文档
collection.update_one({"name": "John"}, {"$set": {"age": 26}})

# 删除文档
collection.delete_one({"name": "John"})
```

这仅仅是一个基本的示例，`pymongo`提供了许多其他功能和操作，建议查阅 [`pymongo`官方文档](https://pymongo.readthedocs.io/) 以获取更详细的信息。