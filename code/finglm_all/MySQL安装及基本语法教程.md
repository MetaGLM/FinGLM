# MySQL安装、基本语法教程及Python调用MySQL

## 目录

- [安装](#安装)
  - [MySQL 安装](#mysql-安装)
    - [Windows](#windows)
    - [macOS (使用Homebrew)](#macos-使用homebrew)
    - [Ubuntu](#ubuntu)
  - [启动MySQL](#启动mysql)
- [基本语法](#基本语法)
  - [连接到MySQL](#连接到mysql)
  - [基本命令](#基本命令)
- [使用Python调用MySQL](#使用python调用mysql)
  - [安装mysql-connector-python](#安装mysql-connector-python)
  - [Python代码示例](#python代码示例)

## 安装

### MySQL 安装

首先，根据您的操作系统，访问 [MySQL官方下载页面](https://dev.mysql.com/downloads/mysql/) 以获取相应版本的安装文件。

#### Windows

1. 下载适合的安装包后，双击打开并按照提示完成安装。
2. 在安装过程中，会提示您设置`root`用户的密码，请妥善保管。

#### macOS (使用Homebrew)

```bash
brew install mysql
```

#### Ubuntu

```bash
sudo apt-get update
sudo apt-get install mysql-server
```

### 启动MySQL

#### Windows

通常，MySQL会作为服务自动启动。您可以在服务中查找MySQL服务进行管理。

#### macOS 和 Ubuntu

```bash
sudo systemctl start mysql
```

## 基本语法

### 连接到MySQL

使用`mysql`命令连接到本地MySQL实例：

```bash
mysql -u root -p
```
输入密码后即可。

### 基本命令

1. **查看所有数据库**:
   ```sql
   SHOW DATABASES;
   ```

2. **选择或创建数据库**:
   ```sql
   USE yourDatabaseName;
   CREATE DATABASE newDatabaseName;
   ```

3. **查看当前数据库中的表**:
   ```sql
   SHOW TABLES;
   ```

4. **插入数据**:
   ```sql
   INSERT INTO yourTableName (column1, column2) VALUES (value1, value2);
   ```

5. **查询数据**:
   ```sql
   SELECT * FROM yourTableName;
   ```

... _(此处可以继续添加更多的SQL基本命令)_ ...

## 使用Python调用MySQL

要在Python中连接和操作MySQL，我们通常使用`mysql-connector-python`库。

### 安装mysql-connector-python

```bash
pip install mysql-connector-python
```

### Python代码示例

```python
import mysql.connector

# 创建连接
conn = mysql.connector.connect(user='root', password='yourPassword', host='127.0.0.1', database='yourDatabaseName')

cursor = conn.cursor()

# 查询数据
cursor.execute("SELECT * FROM yourTableName")
results = cursor.fetchall()
for row in results:
    print(row)

cursor.close()
conn.close()
```

这仅仅是一个基本的示例，`mysql-connector-python`提供了许多其他功能和操作，建议查阅 [`mysql-connector-python`官方文档](https://pypi.org/project/mysql-connector-python/) 以获取更详细的信息。