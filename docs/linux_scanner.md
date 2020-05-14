## Linux环境下安装scanner端指南（以下操作均在centos 7上进行）


### 1. 安装python依赖库

```
# git clone https://github.com/zj1244/beholder_scanner.git
# cd beholder_scanner
# pip install -r requirements.txt
```

### 2. 安装nmap（已安装跳过）

```
# rpm -vhU https://nmap.org/dist/nmap-7.80-1.x86_64.rpm
# nmap -V //输出nmap版本号为成功
```



### 4. 修改配置文件

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
SCAN_TIMEOUT=os.environ.get("SCAN_TIMEOUT", 600)

# redis配置，需按照实际情况修改
REDIS_IP = os.environ.get("REDIS_IP", "127.0.0.1")  # redis的ip
REDIS_PORT = str(os.environ.get("REDIS_PORT", "6379"))  # redis的端口
REDIS_PWD = os.environ.get("REDIS_PWD", "pwd")  # redis的连接密码
VULSCAN_KEY = ""  # 用于后续扫描的队列，保持默认为空即可

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

### 6. 启动

在程序目录下执行如下命令：

```
# python main.py
```

