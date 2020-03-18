# redis安装过程
添加epel，然后安装redis数据库
```
# yum install -y epel-release
# yum install -y redis
```
修改redis.conf
- 允许远程连接：
```
# vi /etc/redis.conf
bind 0.0.0.0
```
- 设置密码，去掉#requirepass foobared的注释即可设置密码。此处设置成pwd：
```
requirepass pwd
```
启动redis并设置成开机自启动:
```
systemctl start redis.service
systemctl enable redis.service
```

