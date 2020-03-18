#!/usr/bin/env python
# coding: utf-8
import os
from scanner.lib.utils.pyredis import PyRedis

from scanner.lib.utils.log_handle import Log

log = Log()

try:
    from config import *
except ImportError:
    log.warning("请检查是否把scanner/config.py.sample复制成scanner/config.py")
    os._exit(0)
redis = PyRedis(hostname=REDIS_IP, port=REDIS_PORT, password=REDIS_PWD)
