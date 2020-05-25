#!/usr/bin/env python
# coding: utf-8
import sys
import os
from scanner import redis, log

import multiprocessing
import threading
from time import sleep, time
from scanner.lib.utils.common import save_setting, load_setting,check_heartbeat
from scanner.lib.utils.common import run_nmap, diff_port


class ChildProcess(multiprocessing.Process):
    def __init__(self, scan_key, scan_data):
        multiprocessing.Process.__init__(self)
        self.scan_key = scan_key
        self.scan_data = scan_data

    def run(self):
        p = multiprocessing.Process(target=run_nmap, args=(self.scan_key, self.scan_data,))
        p.start()
        p.join(60 * 4)
        os._exit(0)


class ParentsProcess(multiprocessing.Process):
    def __init__(self):
        multiprocessing.Process.__init__(self)

    def run(self):

        while True:
            try:
                ack_key = redis.get_key("ack_scan_*")

                if len(ack_key):
                    timeout_data = redis.zrangebyscore(ack_key[0], "-INF", time() - 60 * 5, 0, 1)
                    if timeout_data:
                        log.debug("ack:%s" % timeout_data[0])
                        redis.zrem(ack_key[0], timeout_data[0])
                        redis.put(ack_key[0].replace("ack_scan_", "scan_"), timeout_data[0])
                scan_key = redis.get_key("scan_*")
                if len(scan_key):
                    scanning_num = load_setting().get("scanning_num", 5)

                    if len(multiprocessing.active_children()) < scanning_num:
                        log.debug("【nmap】指定最大并发进程数%s，当前空闲进程数：%s，当前nmap待检测任务数：%s" % (
                            scanning_num, scanning_num - len(multiprocessing.active_children()),
                            redis.qsize(scan_key[0])))
                        log.debug("子进程数目：%s" % len(multiprocessing.active_children()))
                        scan_data = redis.get(scan_key[0])
                        p = ChildProcess(scan_key[0], scan_data)
                        p.start()

                    else:
                        sleep(1)
                else:
                    sleep(1)
                    break
            except Exception as e:

                log.exception(e)
                sleep(60 * 5)


if __name__ == "__main__":

    # test = Nmap()

    for func in [diff_port, save_setting,check_heartbeat]:
        t1 = threading.Thread(target=func)
        t1.setDaemon(True)
        t1.start()
    log.info("扫描开始")
    while True:

        try:
            p = ParentsProcess()
            p.start()
            p.join()

        except Exception as e:
            log.exception(e)
