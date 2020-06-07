## Docker 下快速安装 Demo 版

### 1. 新建文件夹

```
# mkdir -p /mongodb/db
```

### 2. 构建容器

新建个docker_demo.yml文件，复制粘贴如下内容：

```
version: '3'
services:
  scanner:
    image: zj1244/beholder_scanner:latest
    container_name: beholder_scanner
    restart: always
    environment:
      REDIS_IP: redis
      REDIS_PORT: 6379
      REDIS_PWD: ""
      MONGO_IP: mongo
      MONGO_PORT: 27017
      MONGO_USER: ""
      MONGO_PWD: ""
      SCAN_TIMEOUT: 300
      VULSCAN_KEY: ""
    depends_on:
      - redis
      - mongo
  web:
    image: zj1244/beholder_web:latest
    container_name: beholder_web
    ports:
      - "8000:8000"
    restart: always
    environment:
      ACCOUNT: "admin"
      PASSWORD: "admin"
      REDIS_IP: redis
      REDIS_PORT: 6379
      REDIS_PWD: ""
      MONGO_IP: mongo
      MONGO_PORT: 27017
      MONGO_USER: ""
      MONGO_PWD: ""
    depends_on:
      - redis
      - mongo
  redis:
    image: redis:5.0.3
    container_name: beholder_redis
    restart: always
    expose:
      - "6379"
  mongo:
    image: mongo:3.6.15-xenial
    container_name: beholder_mongo
    restart: always
    volumes:
      - "/mongodb/db:/data/db"
    expose:
      - "27017"

```

### 3. 启动容器

```
# docker-compose -f docker_demo.yml up -d
```

### 4. 检查启动是否成功
如果输出类似信息则启动成功，此时可访问[http://ip:8000](http://ip:8000)，输入默认用户名密码admin来登陆
```bash
# docker logs beholder_web
[2020-03-18 Wednesday 00:20] [INFO] Scheduler started
[2020-03-18 Wednesday 00:20] [DEBUG] Looking for jobs to run
[2020-03-18 Wednesday 00:20] [INFO]  * Running on http://0.0.0.0:8000/ (Press CTRL+C to quit)
[2020-03-18 Wednesday 00:20] [DEBUG] Next wakeup is due at 2020-03-18 01:11:13.959033+08:00 (in 3019.861167 seconds)
# docker logs beholder_scanner
[2020-03-18 00:20:52,385] [INFO] 扫描开始
```
