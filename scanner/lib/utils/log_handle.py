#!/usr/bin/env python
# coding: utf-8
import logging, sys, subprocess


class Log(object):
    def __init__(self, save_filename="scan.log"):
        self.BLACK, self.RED, self.GREEN, self.YELLOW, self.BLUE, self.MAGENTA, self.CYAN, self.WHITE = range(8)
        self.RESET_SEQ = "\033[0m"
        self.COLOR_SEQ = "\033[1;%dm"
        self.BOLD_SEQ = "\033[1m"
        self.COLORS = {
            'WARNING': self.YELLOW,
            'INFO': self.GREEN,
            'DEBUG': self.BLUE,
            'CRITICAL': self.RED,
            'ERROR': self.RED,
            'EXCEPTION': self.RED
        }
        logging.basicConfig(
            level=logging.DEBUG,
            format='[%(asctime)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %A %H:%M',
            filename=save_filename,
            filemode='w')
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            console = logging.StreamHandler()

            console.setLevel(logging.DEBUG)  # 配置输出级别
            formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s')

            console.setFormatter(formatter)
            logger.addHandler(console)
        self.logger = logger

    def info(self, msg):
        self.logger.handlers[0].formatter._fmt = self.COLOR_SEQ % (
            30 + self.COLORS['INFO']) + '[%(asctime)s] [%(levelname)s] %(message)s' + self.RESET_SEQ
        self.logger.info(msg)
        pass

    def warning(self, msg):
        self.logger.handlers[0].formatter._fmt = self.COLOR_SEQ % (
            30 + self.COLORS['WARNING']) + '[%(asctime)s] [%(levelname)s] %(message)s' + self.RESET_SEQ
        self.logger.warning(msg)

    def error(self, msg):
        self.logger.handlers[0].formatter._fmt = self.COLOR_SEQ % (
            30 + self.COLORS['ERROR']) + '[%(asctime)s] [%(levelname)s] %(message)s' + self.RESET_SEQ
        self.logger.error(msg)

    def critical(self, msg):
        self.logger.handlers[0].formatter._fmt = self.COLOR_SEQ % (
            30 + self.COLORS['CRITICAL']) + '[%(asctime)s] [%(levelname)s] %(message)s' + self.RESET_SEQ
        self.logger.critical(msg)

    def debug(self, msg):
        self.logger.handlers[0].formatter._fmt = self.COLOR_SEQ % (
            30 + self.COLORS['DEBUG']) + '[%(asctime)s] [%(levelname)s] %(message)s' + self.RESET_SEQ
        self.logger.debug(msg)

    def exception(self, msg):
        self.logger.handlers[0].formatter._fmt = self.COLOR_SEQ % (
            30 + self.COLORS['EXCEPTION']) + '[%(asctime)s] [%(levelname)s] %(message)s' + self.RESET_SEQ
        self.logger.exception(msg)




if __name__ == '__main__':
    # if not subprocess.mswindows and sys.stdout.isatty():
    Log().info("dddddd")
    my_log = Log()  #
    my_log.info("1")
    my_log.warning("2")
    my_log.error("3")
    my_log.debug("4")
    try:
        xxx()
    except:
        my_log.exception("aa")
