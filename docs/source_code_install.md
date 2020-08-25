## 源码部署

安装分两大部分，分别是：
* 安装 beholder_scanner
* 安装 beholder_web

### 依赖条件：

项目运行依赖于mongodb和redis，所以需准备好mongodb和redis。   
 
mongodb和redis安装请参考：

* [mongodb安装](./mongodb.md)
* [redis安装](./redis.md)

***

### 安装beholder_scanner：

#### 1. 添加mongodb认证

**在 mongodb 服务器上**新建 db 用户，这里新建了一个用户名为`scan`密码为`123456`的用户。

```
# mongo
> use admin
> db.createUser({user:'scan',pwd:'123456', roles:[{role:'readWriteAnyDatabase', db:'admin'}]})
> exit
```

#### 2. 导入数据库

把beholder_scanner项目下的`db`文件夹导入 mongodb 。**在 mongodb 服务器上**执行如下命令：

```
# git clone https://github.com/zj1244/beholder_scanner.git
# cd beholder_scanner/db/
# mongorestore -u scan -p 123456 --authenticationDatabase admin -d portscan .
```

#### 3. 安装python依赖库

```
# git clone https://github.com/zj1244/beholder_scanner.git
# cd beholder_scanner
# pip install -r requirements.txt
```

#### 4. 安装nmap（如已安装跳过）

```
# rpm -vhU https://nmap.org/dist/nmap-7.80-1.x86_64.rpm
# nmap -V //输出nmap版本号为成功
```

#### 5. 修改配置文件

首先将`config.py.sample`复制一份重命名为`config.py`
```
# cp scanner/config.py.sample scanner/config.py

```

然后按照自己的要求修改配置：

```
# coding=utf-8
import os

# 1是ping发现主机，0是通过发送tcp syn包到指定端口来发现主机
FIND_HOST = os.environ.get("FIND_HOST", 1)
# 扫描超时设置，单位秒
SCAN_TIMEOUT=int(os.environ.get("SCAN_TIMEOUT", 300))

# redis配置，需按照实际情况修改
REDIS_IP = os.environ.get("REDIS_IP", "127.0.0.1")  # redis的ip
REDIS_PORT = str(os.environ.get("REDIS_PORT", "6379"))  # redis的端口
REDIS_PWD = os.environ.get("REDIS_PWD", "pwd")  # redis的连接密码
VULSCAN_KEY = os.environ.get("VULSCAN_KEY", "pwd")  # 用于后续扫描的队列，没后续扫描则保留为空

# db配置，需按照实际情况修改
MONGO_IP = os.environ.get("MONGO_IP", "127.0.0.1")  # mongodb的ip
MONGO_PORT = int(os.environ.get("MONGO_PORT", 27017))  # mongodb的端口
MONGO_USER = os.environ.get("MONGO_USER", "scan")  # mongodb的用户名
MONGO_PWD = os.environ.get("MONGO_PWD", "123456")  # mongodb的密码

# 可以保持默认
MONGO_DB_NAME = "portscan"
MONGO_TASKS_COLL_NAME = "tasks"
MONGO_RESULT_COLL_NAME = "scan_result"
MONGO_SETTING_COLL_NAME = "setting"

```

#### 6. 启动

在程序目录下执行如下命令：

```
# python main.py
```

### 安装beholder_web：

#### 1. 安装python依赖库

```
# git clone https://github.com/zj1244/beholder_web.git
# cd beholder_web
# pip install -r requirements.txt
```

#### 2. 修改配置文件

首先将`config.env.sample`复制一份重命名为`config.env`
```
# cp config.env.sample config.env
```

然后修改登陆用户名密码、mongodb和redis连接配置：

```
# username and password
ACCOUNT="admin"
PASSWORD="admin"

# databases
MONGO_IP = "192.168.47.168"
MONGO_PORT = 27017
MONGO_USER = "scan"
MONGO_PWD = "123456"
MONGO_DB_NAME = "portscan"

# redis
REDIS_IP = "192.168.47.168"
REDIS_PORT = "6379"
REDIS_PWD = "pwd"
```

#### 3. 启动

在程序目录下执行如下命令：

```
# python main.py
```
