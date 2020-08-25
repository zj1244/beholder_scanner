# beholder 

**beholder**是一款简洁而小巧的系统，主要作用是通过监控端口变化来发现企业内部的信息孤岛。例如：运维或开发新部署了一台机器未通知安全。没有采用masscan+nmap的组合进行检测，原因是在实际的使用中发现，虽然masscan可以提高扫描速度，但是漏报的情况太严重了。最终还是只使用nmap来进行探测。

系统由 `beholder_scanner`、 `beholder_web`  两个部分组成。这两个部分可以部署在一台机器上，也可以分开部署在不同的机器上。**当前项目为 `beholder_scanner`部分**。`beholder_web`部分可以查看[这里](https://github.com/zj1244/beholder_web)

* **beholder_scanner**：对IP进行端口扫描、比较端口变化，可部署多个beholder_scanner来组成集群加快扫描速度。
* **beholder_web**：提供前端界面展示。

## 支持任务

* 常规扫描：一次性的普通端口扫描任务
* 比较端口变化：用于比较两次扫描结果的端口变化
* 监控端口开放情况：一般用于监控IP是否开放高危端口，如开放则告警

## 支持平台

* Linux
* Windows

## 安装指南

[![Python 2.7](https://img.shields.io/badge/python-2.7-yellow.svg)](https://www.python.org/) 
[![Mongodb 3.x](https://img.shields.io/badge/mongodb-3.x-red.svg)](https://www.mongodb.com/download-center?jmp=nav)
[![Redis 3.x](https://img.shields.io/badge/redis-3.x-green)](https://redis.io/)

总共有三种安装方式，分别是：

1. [Demo版部署](docs/docker_demo.md)
2. [源码部署](docs/source_code_install.md)
3. [基于docker的分布式部署](docs/distributed.md)
