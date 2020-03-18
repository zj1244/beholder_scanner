# coding=utf-8
import redis


class PyRedis(object):
    def __init__(self, hostname='localhost', port=6379, db=0, password=''):
        """
        连接数据库
        :param name:对应redis的数据库的键
        :param namespace:
        :return:
        """

        self.pool = redis.ConnectionPool(host=hostname, port=port, db=db, password=password)
        self.__db = redis.Redis(connection_pool=self.pool)
        pass

    def qsize(self, key):
        """
        对应键的大小
        :return:
        """
        return self.__db.llen(key)

    def empty(self, key):
        """
        是否为空
        :return:
        """
        return self.qsize(key) == 0

    def put(self, key, values):
        """
        放进对应键的值，插入
        :param item:
        :return:
        """
        try:
            return self.__db.lpush(key, values)
        except Exception, e:
            print "error:%s" % e

    def sadd(self, key, values):
        """
        放进对应键的值，插入
        :param item:
        :return:
        """
        try:
            return self.__db.sadd(key, values)
        except Exception, e:
            print "error:%s" % e

    def spop(self, key):
        """
        移除并返回集合中的一个随机元素
        :param item:
        :return:
        """
        try:
            return self.__db.spop(key)
        except Exception, e:
            print "error:%s" % e

    def pipe(self):
        return self.__db.pipeline()

    def get(self, key, block=True, timeout=0):
        """
        """
        if block:
            item = self.__db.blpop(key, timeout=timeout)
            # PyRedis Blpop 命令移出并获取列表的第一个元素， 如果列表没有元素会阻塞列表直到等待超时或发现可弹出元素为止。
            # 如果列表为空，返回一个 nil 。 否则，返回一个含有两个元素的列表，第一个元素是被弹出元素所属的 key ，第二个元素是被弹出元素的值。
            if item:
                item = item[1]
        else:
            # PyRedis Lpop 命令用于移除并返回列表的第一个元素。
            item = self.__db.lpop(key)

        return item

    def get_lrange(self, key, start, end):
        """
        取对应位置的值
        :param end:
        :return:
        """
        return self.__db.lrange(key, start, end)

    def del_key(self, key):
        """
        删除键
        :return:
        """
        self.__db.delete(key)

    def exists_key(self, key):
        """
        判断是否存在
        """
        return self.__db.exists(key) == 1

    def get_key(self, key_pattern):
        """
        获取模式下的键
        """
        return self.__db.keys(key_pattern)

    ###########################
    def hexists(self, hash_name, key):
        """
        指定字段是否存在
        :return:
        """
        return self.__db.hexists(hash_name, key)

    def hlen(self, hash_name):
        """
        对应哈希字段的大小
        :return:
        """
        return self.__db.hlen(hash_name)

    def hset(self, hash_name, key, value):
        return self.__db.hset(hash_name, key, value)

    def hget(self, hash_name, key):
        return self.__db.hget(hash_name, key)

    def hgetall(self, hash_name):
        """
        取对应位置的值
        :param end:
        :return:
        """
        return self.__db.hgetall(hash_name)

    def hdel(self, hash_name, key):
        """
        删除键
        :return:
        """
        return self.__db.hdel(hash_name, key)

    #######################
    def zadd(self, key, mapping):
        return self.__db.zadd(key, mapping)

    def zrem(self, key, member):
        return self.__db.zrem(key, member)

    def zrangebyscore(self, key, min, max, start=None, num=None,
                      withscores=False, score_cast_func=float):
        return self.__db.zrangebyscore(key, min, max, start, num, withscores, score_cast_func)

    def zremrangebyscore(self, key, min, max):
        return self.__db.zremrangebyscore(key, min, max)

    def publish(self,channel,msg):
        return self.__db.publish(channel,msg)

    def subscribe(self,channel):
        pub=self.__db.pubsub()
        pub.subscribe(channel)
        pub.listen()

        return pub



if __name__ == '__main__':
    from scanner.config import *

    b =  [('x', 108.0), ('b', 4.0)]
    score1 = 10

    data2 = "bar"
    score2 = 20

    redis_queue = PyRedis(hostname=REDIS_IP, port=REDIS_PORT, password=REDIS_PWD)
    # redis_queue.del_key("scan_5c989f07e8123c748804de4f")
    #
    a = redis_queue.zadd("ack_scan_5c989f07e8123c748804de4f", {"a":1})
    a = redis_queue.zremrangebyscore("ack_scan_5c989f07e8123c748804de4f", "-INF", "+INF")


