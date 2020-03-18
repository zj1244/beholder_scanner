## 部署mongodb和redis（如已安装跳过）

* [mongodb安装](./docs/mongodb.md)
* [redis安装](./docs/redis.md)

## 部署 beholder_web和beholder_scanner

### 1. 构建镜像&&启动容器

新建个install_web_and_scanner.yml文件，复制粘贴如下内容：

```
version: '3'
services:
  scanner:
    image: zj1244/beholder_scanner:latest
    restart: always
    environment:
      # 请修改以下redis和mongodb的配置
      REDIS_IP: 192.168.47.168
      REDIS_PORT: 6379
      REDIS_PWD: pwd
      MONGO_IP: 192.168.47.168
      MONGO_PORT: 27017
      MONGO_USER: scan
      MONGO_PWD: 123456
  web:
    image: zj1244/beholder_web:latest
    ports:
      - "8000:8000"
    restart: always
    environment:
      # 登陆用户名密码
      ACCOUNT: "admin"
      PASSWORD: "123456"
      # 请修改以下redis和mongodb的配置
      REDIS_IP: 192.168.47.168
      REDIS_PORT: 6379
      REDIS_PWD: pwd
      MONGO_IP: 192.168.47.168
      MONGO_PORT: 27017
      MONGO_USER: scan
      MONGO_PWD: 123456
```

### 2. 启动容器

```
# docker-compose -f install_web_and_scanner.yml up -d
```

### 3. 检查启动是否成功
如果输出类似信息则启动成功，此时可访问[http://ip:8000](http://ip:8000)，输入install_web_and_scanner.yml里的用户名密码来登陆
```bash
# docker logs beholder_web
[2020-03-18 Wednesday 00:20] [INFO] Scheduler started
[2020-03-18 Wednesday 00:20] [DEBUG] Looking for jobs to run
[2020-03-18 Wednesday 00:20] [INFO]  * Running on http://0.0.0.0:8000/ (Press CTRL+C to quit)
[2020-03-18 Wednesday 00:20] [DEBUG] Next wakeup is due at 2020-03-18 01:11:13.959033+08:00 (in 3019.861167 seconds)
# docker logs beholder_scanner
[2020-03-18 00:20:52,385] [INFO] 扫描开始
```


至此整套程序部署完毕，如果需要部署多个scanner可以参考以下步骤

## 部署单个 beholder_scanner

在多个主机上重复部署beholder_scanner提高扫描速度。

### 1. 构建镜像&&启动容器

使用 vi 新建一个名为docker-compose.yml的文件，文件内容如下：

```
# vi docker-compose.yml # 第一步，使用 vi 新建一个名为docker-compose.yml的文件，文件内容如下：
version: '3'
services:
  scanner:
    image: zj1244/beholder_scanner:latest
    restart: always
    environment:
      # 请修改以下redis和mongodb的配置
      REDIS_IP: 192.168.47.168
      REDIS_PORT: 6379
      REDIS_PWD: pwd
      MONGO_IP: 192.168.47.168
      MONGO_PORT: 27017
      MONGO_USER: scan
      MONGO_PWD: 123456
# docker-compose up -d # 第二步，启动镜像
```

**或者**

请按照实际情况修改 docker-compose.yml 文件里关于redis和mongodb的信息。
```
# git clone https://github.com/zj1244/beholder_scanner.git
# cd beholder_scanner
# vi docker-compose.yml #需要修改redis和mongodb的配置信息
# docker-compose up -d
```

### 2. 检查scanner是否正常启动
输入如下命令，如果输出`扫描开始`则表示启动成功
```
# docker logs $(docker ps | grep beholder_scanner | awk '{print $1}')
[2020-02-15 15:48:56,575] [INFO] 扫描开始
```