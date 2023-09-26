# SQLite 安装及基本语法教程

## 目录

- [安装](#安装)
- [基本语法](#基本语法)
- [使用Python调用SQLite](#使用python调用sqlite)
  - [安装sqlite3](#安装sqlite3)
  - [Python代码示例](#python代码示例)

## 安装

SQLite是一个服务器less的数据库，这意味着与其他数据库不同，SQLite不需要安装服务或守护进程。您只需要下载一个可执行的二进制文件。

您可以从 [SQLite官方下载页面](https://www.sqlite.org/download.html) 获取最新的预编译的二进制文件。

### Windows

1. 下载 "sqlite-tools-win32-x86-xxxx.zip" 并解压。
2. 将解压的文件夹添加到系统的`PATH`变量中，以便从命令行访问。

### macOS 和 Ubuntu

SQLite通常在macOS和Ubuntu上预装。您可以通过以下命令检查其版本：

```bash
sqlite3 --version
```

## 基本语法

启动SQLite CLI：

```bash
sqlite3 yourDatabaseName.db
```

### 基本命令

1. **查看所有表**:
   ```sql
   .tables
   ```

2. **创建表**:
   ```sql
   CREATE TABLE yourTableName (column1 datatype, column2 datatype);
   ```

3. **插入数据**:
   ```sql
   INSERT INTO yourTableName (column1, column2) VALUES (value1, value2);
   ```

4. **查询数据**:
   ```sql
   SELECT * FROM yourTableName;
   ```

... _(此处可以继续添加更多的SQLite基本命令)_ ...

## 使用Python调用SQLite

Python标准库中包含了`sqlite3`模块，所以不需要额外安装。

### Python代码示例

```python
import sqlite3

# 创建连接
conn = sqlite3.connect('yourDatabaseName.db')

cursor = conn.cursor()

# 创建表
cursor.execute('''CREATE TABLE yourTableName
                  (column1 datatype, column2 datatype)''')

# 插入数据
cursor.execute("INSERT INTO yourTableName VALUES (value1, value2)")

# 提交改动
conn.commit()

# 查询数据
cursor.execute("SELECT * FROM yourTableName")
results = cursor.fetchall()
for row in results:
    print(row)

cursor.close()
conn.close()
```

这仅仅是一个基本的示例，Python的`sqlite3`模块提供了许多其他功能和操作，建议查阅 [`sqlite3`官方文档](https://docs.python.org/3/library/sqlite3.html) 以获取更详细的信息。
