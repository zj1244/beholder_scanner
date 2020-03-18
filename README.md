# beholder 

**beholder**是一款简洁而小巧的系统，主要作用是通过监控端口变化来发现企业内部的信息孤岛。例如：运维或开发新部署了一台机器未通知安全。

系统由 `beholder_scanner`、 `beholder_web`  两个部分组成。这两个部分可以部署在一台机器上，也可以分开部署在不同的机器上。**当前项目为 `beholder_scanner`部分**。

* **beholder_scanner**：对IP进行端口扫描、比较端口变化，可部署多个beholder_scanner来组成集群加快扫描速度。
* **beholder_web**：提供前端界面展示。

## 支持平台

* Linux
* Windows

## 安装指南

[![Python 2.7](https://img.shields.io/badge/python-2.7-yellow.svg)](https://www.python.org/) 
[![Mongodb 3.x](https://img.shields.io/badge/mongodb-3.x-red.svg)](https://www.mongodb.com/download-center?jmp=nav)
[![Redis 3.x](https://img.shields.io/badge/redis-3.x-green)](https://redis.io/)

### Demo版部署

如果只是测试和尝鲜可以部署Demo版：

优点是部署简单，缺点是不利于扩展和管理。

* [Docker下安装Demo版](docs/docker_demo.md)

***

### 常规部署

**依赖：项目运行依赖于mongodb和redis，所以需准备好mongodb和redis，mongodb和redis安装请参考：**

* [mongodb安装](./docs/mongodb.md)
* [redis安装](./docs/redis.md)

**常规部署**步骤如下：

***

#### 1. 添加mongodb认证

**在 mongodb 服务器上**新建 db 用户，这里新建了一个用户名为`scan`密码为`123456`的用户。

```
# mongo
> use admin
> db.createUser({user:'scan',pwd:'123456', roles:[{role:'readWriteAnyDatabase', db:'admin'}]})
> exit
```

#### 2. 导入数据库

**把本项目下的`db`文件夹复制到 mongodb 所在机器**，进入`db`文件夹，执行如下命令：

```
# mongorestore -u scan -p 123456 --authenticationDatabase admin -d portscan .
```

#### 3. 选择

此时你有两个选择：

##### 选择一：

**源码部署请参考：**

如准备好了mongodb和redis，只需要部署scanner和web即可。

* [Linux下安装beholder_scanner指南](./docs/linux_scanner.md)
* [Linux下安装beholder_web指南](https://github.com/zj1244/beholder_web/blob/master/docs/linux_web.md)

##### 选择二：

**分布式部署请参考：**

建议准备至少两台机器，把mongodb和redis安装在一台机器上，另一台机器安装web端和scanner端。

* [分布式部署](./docs/distributed.md)