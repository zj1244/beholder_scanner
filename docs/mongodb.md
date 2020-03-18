# mongodb安装过程
```
# vi /etc/yum.repos.d/mongodb-org-4.repo
```

输入如下内容:

```
[mongodb-org-4.0]
name=MongoDB Repository
baseurl=https://repo.mongodb.org/yum/redhat/$releasever/mongodb-org/4.0/x86_64/
gpgcheck=1
enabled=1
gpgkey=https://www.mongodb.org/static/pgp/server-4.0.asc
```

保存并退出，执行如下命令:

```
# yum install -y mongodb-org
```

配置mongod.conf允许远程连接：
```
# vi /etc/mongod.conf
bind_ip = 0.0.0.0
```
保存并退出后，启动mongodb并设置成开机自启动：
```
# systemctl start mongod.service
# systemctl enable mongod.service
```
执行如下命令查看mongodb是否成功启动:
```
# netstat -antlp | grep 27017
```
