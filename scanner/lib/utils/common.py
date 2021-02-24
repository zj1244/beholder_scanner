# !/usr/bin/env python
# -*- coding: utf-8 -*-
import datetime
import sys
import struct
import socket

import json
from scanner.config import *

from time import sleep, strftime, localtime, time
from bson.objectid import ObjectId
from scanner import redis, log
from scanner.lib.utils.mongodb import Mongodb
from scanner.lib.utils.portscan import Nmap

reload(sys)
sys.setdefaultencoding('utf8')
try:
    from mailer import Mailer
    from mailer import Message
except ImportError:
    log.warning("error Missing Mailer")


def check_heartbeat():
    redis.hset(hash_name="beholder_node", key=get_node_ip(), value=time())
    sleep(60 * 5)


def get_setting_path():
    setting_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../.."))
    setting_path = os.path.join(setting_path, "setting.json")
    return setting_path


def save_setting():
    setting = {
    }
    while True:
        try:
            mongo = Mongodb(host=MONGO_IP, port=MONGO_PORT, username=MONGO_USER, password=MONGO_PWD)
            result = mongo.conn[MONGO_DB_NAME][MONGO_SETTING_COLL_NAME].find_one({})
            if result:
                setting_path = get_setting_path()

                for key in ["mail_enable", "scanning_num", "email_address", "email_pwd", "email_server", "sender"]:
                    setting[key] = result.get(key, "")

                with open(setting_path, "w+") as fp:
                    fp.write(dict2str(setting))
        except Exception as e:
            log.exception("save setting failed : %s" % e)
        sleep(60)


def load_setting():
    setting_path = get_setting_path()
    if os.path.exists(setting_path):
        with open(setting_path) as fp:
            return str2dict(fp.read())
    else:

        log.info("未找到setting.json")
        return {}


def send_mail(subject, contents, host, use_ssl, sender, pwd, email_address):
    message = Message(From=sender,
                      To=email_address, charset="utf-8")
    message.Subject = subject
    message.Html = contents
    if sender[sender.find("@") + 1:] in host:
        sender = sender[:sender.find("@")]
    mailer = Mailer(host=host, use_ssl=use_ssl, usr=sender,
                    pwd=pwd)

    mailer.send(message, debug=False)

    log.info("sender:%s,to=%s" % (sender, email_address))


def ip_atoi(ip):
    return struct.unpack('!I', socket.inet_aton(ip))[0]


def ip_itoa(ip):
    return socket.inet_ntoa(struct.pack('!I', ip))


def get_ip_list(start_ip, end_ip):
    ip_list = []
    start_ip = ip_atoi(start_ip)
    end_ip = ip_atoi(end_ip) + 1
    for ip in range(start_ip, end_ip):
        ip_list.append(ip_itoa(ip))
    return ip_list


def get_node_ip(ip="8.8.8.8", port=80):
    csock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    csock.connect((ip, port))
    (addr, port) = csock.getsockname()
    csock.close()
    return addr


def str2dict(string):
    try:
        if type(string) == dict:
            return string
        return json.loads(string)
    except TypeError as e:
        log.exception("conv string failed : %s" % e)


def dict2str(dictionary):
    try:
        if type(dictionary) == str:
            return dictionary
        return json.dumps(dictionary)
    except TypeError as e:
        log.exception("conv dict failed : %s" % e)


def run_nmap(scan_key, scan_data):
    try:
        redis.zadd("ack_" + scan_key, {scan_data: time()})

        nm = Nmap()
        scan_data_dict = str2dict(scan_data)
        ip = scan_data_dict['ip']
        port = str(scan_data_dict['port'])
        log.debug("pid=%s,nmap开始扫描:%s" % (os.getpid(), scan_data))
        timeout = int(globals().get("SCAN_TIMEOUT", 300))
        if FIND_HOST:
            nm.scan(hosts=ip, arguments='-sV -p%s -T4 --version-intensity 4' % port, timeout=timeout)
        else:
            nm.scan(hosts=ip, arguments='-sV -PS445,22 -p%s -T4 --version-intensity 4' % port, timeout=timeout)

        nmap_result_list = nm.scan_result()
        log.debug("pid=%s,nmap扫描结束:%s" % (os.getpid(), scan_data))
        if nmap_result_list:
            mongo = Mongodb(host=MONGO_IP, port=MONGO_PORT, username=MONGO_USER, password=MONGO_PWD)
            mongo_scan_result = mongo.conn[MONGO_DB_NAME][MONGO_RESULT_COLL_NAME]
            for nmap_result in nmap_result_list:
                nmap_result['port_status'] = 'open'
                nmap_result['base_task_id'] = ObjectId(scan_data_dict['base_task_id'])
                nmap_result['create_time'] = datetime.datetime.now().strftime('%Y-%m-%d')
                nmap_result['ip_port'] = "%s:%s" % (nmap_result['ip'], str(nmap_result['port']))
                if VULSCAN_KEY:
                    redis.sadd(VULSCAN_KEY, json.dumps(
                        {"protocol": nmap_result["service"], "info_id": 0, "finger": nmap_result["version_info"],
                         "type": "portscan", "port": nmap_result["port"], "url": nmap_result["ip"]}))
            mongo_scan_result.insert_many(nmap_result_list, ordered=False)
            mongo.conn.close()
        redis.zrem("ack_" + scan_key, scan_data)

    except KeyboardInterrupt as e:
        log.exception(scan_data)

    except Exception as e:
        log.exception(scan_data)
        redis.zrem("ack_" + scan_key, scan_data)


def task_process():
    while True:
        try:

            mongo = Mongodb(host=MONGO_IP, port=MONGO_PORT, username=MONGO_USER, password=MONGO_PWD)
            mongo_task = mongo.conn[MONGO_DB_NAME][MONGO_TASKS_COLL_NAME]
            mongo_scan_result = mongo.conn[MONGO_DB_NAME][MONGO_RESULT_COLL_NAME]

            cron_task_running = mongo_task.find(
                {"task_status": "running"})

            if cron_task_running.count():
                for t in cron_task_running:

                    if not redis.get_key("scan_" + str(t["_id"])) and not redis.get_key(
                            "ack_scan_" + str(t["_id"])):
                        log.info("扫描结束")
                        mongo_task.update_one({"_id": t["_id"]},
                                              {"$set": {"task_status": "finish", "end_time": datetime.datetime.now()}})

            task_names = mongo_task.aggregate(
                [{"$match": {"task_status": "finish",
                             "$or": [{"diff_result": {"$exists": False}}, {"diff_result.diff": 0},
                                     {"monitor_result.monitor": 0}]}},
                 {"$group": {"_id": "$name", "last_doc": {"$last": "$$ROOT"}}}])

            for task_name in task_names:
                setting = load_setting()

                date = strftime('%Y-%m-%d', localtime())
                if task_name["last_doc"]["task_type"] == "monitor_task":
                    ip_port = set()
                    results = mongo_scan_result.find({"base_task_id": task_name['last_doc']['_id']})
                    for result in results:
                        ip_port.add("%s:%s" % (result['ip'], result['port']))

                    if setting["mail_enable"] == "on":
                        mail_contents = format_monitor_html(scan_time=date, ips_count=len(ip_port), ips=ip_port)
                        if "," in setting["email_address"]:
                            setting["email_address"] = setting["email_address"].split(",")
                        send_mail(subject="【%s】【%s】监控端口开放结果" % (date, task_name['_id']), contents=mail_contents,
                                  host=setting["email_server"],
                                  use_ssl=True,
                                  sender=setting["sender"], pwd=setting["email_pwd"],
                                  email_address=setting["email_address"])

                    mongo_task.update_one({"_id": task_name['last_doc']['_id']}, {
                        "$set": {"monitor_result.monitor": 1, "monitor_result.ip_port": list(ip_port),
                                 }})

                elif task_name["last_doc"]["task_type"] in [ "diff_task","loop"]:
                    tasks = mongo_task.find(
                        {"name": task_name['_id'], "task_status": "finish"}
                    ).sort([('create_time', -1)]).limit(3)
                    if tasks.count() > 2:
                        new_task = tasks[0]
                        lasttime_task_0 = tasks[1]
                        lasttime_task_1 = tasks[2]

                        new_ip_ports, old_ip_ports_1, old_ip_ports_0 = set(), set(), set()
                        new_ips, old_ips_0, old_ips_1 = set(), set(), set()

                        results = mongo_scan_result.find({"base_task_id": new_task['_id']})
                        for result in results:
                            new_ip_ports.add("%s:%s" % (result['ip'], result['port']))
                            new_ips.add(result['ip'])

                        results = mongo_scan_result.find({"base_task_id": lasttime_task_0['_id']})
                        for result in results:
                            old_ip_ports_0.add("%s:%s" % (result['ip'], result['port']))
                            old_ips_0.add(result['ip'])

                        results = mongo_scan_result.find({"base_task_id": lasttime_task_1['_id']})
                        for result in results:
                            old_ip_ports_1.add("%s:%s" % (result['ip'], result['port']))
                            old_ips_1.add(result['ip'])

                        add_ports = new_ip_ports - old_ip_ports_0 - old_ip_ports_1
                        add_ips = new_ips - old_ips_0 - old_ips_1

                        del_ports = old_ip_ports_0 - new_ip_ports
                        del_ips = old_ips_0 - new_ips

                        mongo_task.update_one({"_id": new_task['_id']}, {
                            "$set": {"diff_result.diff": 1, "diff_result.add_ips": list(add_ips),
                                     "diff_result.add_ports": list(add_ports)}})
                        mongo_task.update_many({"name": task_name['_id'], "diff_result.diff": 0}, {
                            "$set": {"diff_result.diff": 1}})

                        if setting["mail_enable"] == "on":
                            contents = format_diff_html(scan_time=date, add_ips_count=len(add_ips),
                                                        add_ports_count=len(add_ports), del_ips_count=len(del_ips),
                                                        add_ips=add_ips, add_ports=add_ports, del_ips=del_ips)
                            if "," in setting["email_address"]:
                                setting["email_address"] = setting["email_address"].split(",")
                            send_mail(subject="【%s】【%s】端口对比结果" % (date, task_name['_id']), contents=contents,
                                      host=setting["email_server"],
                                      use_ssl=True,
                                      sender=setting["sender"], pwd=setting["email_pwd"],
                                      email_address=setting["email_address"])

                    else:
                        log.info("任务是第一次扫描")

                        for task in tasks:
                            mongo_task.update_one({"_id": task['_id']}, {"$set": {"diff_result.diff": 1}})
                else:
                    pass


        except Exception as e:
            log.exception(e)
        sleep(60)


def format_diff_html(scan_time="", add_ips_count=0, add_ports_count=0, del_ips_count=0, add_ips=set(), add_ports=set(),
                     del_ips=set()):
    # 邮件正文

    add_ips_html = ""

    for ip in add_ips:
        add_ips_html += """
         <tr>
        <td style="height: auto; padding: 0px 20px; color: rgb(51, 51, 51); font-size: 13px; border-bottom: 1px solid rgb(238, 238, 238); border-left: 1px solid rgb(238, 238, 238); font-family: &quot;Microsoft YaHei&quot;, SimSun, Tahoma, Verdana, Arial, Helvetica, sans-serif;">%s</td> 
       </tr> """ % ip

    add_ports_html = ""

    for port in add_ports:
        add_ports_html += """
        <tr>
            <td style="height: auto; padding: 0px 20px; color: rgb(51, 51, 51); font-size: 13px; border-bottom: 1px solid rgb(238, 238, 238); border-left: 1px solid rgb(238, 238, 238); font-family: &quot;Microsoft YaHei&quot;, SimSun, Tahoma, Verdana, Arial, Helvetica, sans-serif;">%s</td> 
         </tr>   """ % port

    del_ips_html = ""

    for ip in del_ips:
        del_ips_html += """
        <tr>
            <td style="height: auto; padding: 0px 20px; color: rgb(51, 51, 51); font-size: 13px; border-bottom: 1px solid rgb(238, 238, 238); border-left: 1px solid rgb(238, 238, 238); font-family: &quot;Microsoft YaHei&quot;, SimSun, Tahoma, Verdana, Arial, Helvetica, sans-serif;">%s</td>  
           </tr> """ % ip
    html = """
    <table cellpadding="0" cellspacing="0" style="margin: 0px; padding: 0px; width: 1000px;" _ow="1280px"> 
       <tbody> 
        <tr style="padding:0;"> 
         <td valign="middle" style="padding: 0px 24px; height: auto; width: 100%%; background-color: rgb(20, 158, 204);"> 
          <table bgcolor="#149ECC" cellpadding="0" cellspacing="0" style="padding:0;color:#ffffff;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;"> 
           <tbody> 
            <tr> 
             <td valign="middle" style="height: auto; color: rgb(255, 255, 255); line-height: 20px; font-size: 20px; vertical-align: middle; border: none; padding: 0px; margin: 0px; font-family: &quot;Microsoft YaHei&quot;, SimSun, Tahoma, Verdana, Arial, Helvetica, sans-serif;">端口扫描结果</td> 
             <td style="width: 9px; height: auto; padding: 0px;"></td> 
             <td style="width: 3px; height: auto; padding: 0px; color: rgb(255, 255, 255);">|</td> 
             <td style="width: 9px; height: auto; padding: 0px;"></td> 
             <td style="height: auto; color: rgb(255, 255, 255); line-height: 21px; font-size: 12px; vertical-align: middle; border: none; padding: 0px; margin: 0px; font-family: &quot;Microsoft YaHei&quot;, SimSun, Tahoma, Verdana, Arial, Helvetica, sans-serif;"><span>%s</span></td> 
            </tr> 
           </tbody> 
          </table></td> 
        </tr> 
        <tr> 
         <td valign="middle" style="padding:20.0px 24.0px;width:100.0%%;"> 
          <table cellpadding="0" cellspacing="0" style="width:100.0%%;padding:0;color:#ffffff;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;"> 
           <tbody> 
            <tr> 
             <td bgcolor="#0095b3" style="width: 3px; height: auto; padding: 0px; background-color: rgb(20, 158, 204);"></td> 
             <td style="width: 9px; height: auto; padding: 0px;"></td> 
             <td style="line-height: 20px; color: rgb(66, 66, 66); font-family: &quot;Microsoft YaHei&quot;, SimSun, Tahoma, Verdana, Arial, Helvetica, sans-serif; font-weight: 700; font-size: 16px; height: auto;">结果概述</td> 
            </tr> 
           </tbody> 
          </table></td> 
        </tr> 
        <tr> 
         <td valign="middle" style="padding:0 24.0px 10.0px;width:100.0%%;"> 
          <table cellpadding="0" cellspacing="0" style="width:100.0%%;padding:0;color:#ffffff;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;"> 
           <tbody> 
            <tr> 
             <td width="24%%" style="border: 2px solid rgb(238, 238, 238); height: auto;"> 
              <table cellpadding="0" cellspacing="0" style="border-collapse: collapse; border: none; border-spacing: 0px; margin: 0px; width: 100%%; height: auto; padding: 0px;"> 
               <tbody> 
                <tr> 
                 <td style="width: 100px; height: auto; padding: 0px 0px 0px 30px; background-color: rgb(238, 238, 238); color: rgb(51, 51, 51); font-weight: 700; font-size: 14px;">新增IP</td> 
                 <td style="height: auto; background-color: rgb(238, 238, 238); text-align: right;"></td> 
                </tr> 
                <tr> 
                 <td style="width:50.0%%;"> 
                  <table cellpadding="0" cellspacing="0" style="width:auto;padding:0;border-collapse:collapse;"> 
                   <tbody> 
                    <tr> 
                     <td valign="top" style="padding:0 10.0px 8.0px 30.0px;border:none;font-size:12.0px;color:#333333;vertical-align:top;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;">总数</td> 
                    </tr> 
                    <tr> 
                     <td colspan="2" style="padding:0 0 0 30.0px;font-size:28.0px;color:#333333;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;">%s</td> 
                    </tr> 
                   </tbody> 
                  </table></td> 
                 <td style="width:50.0%%;"></td> 
                </tr> 
               </tbody> 
              </table></td> 
             <td style="width: 30px; height: auto;"></td> 
             <td width="24%%" style="border: 2px solid rgb(238, 238, 238); height: auto;"> 
              <table cellpadding="0" cellspacing="0" style="border-collapse: collapse; border: none; border-spacing: 0px; margin: 0px; width: 100%%; height: auto; padding: 0px;"> 
               <tbody> 
                <tr> 
                 <td style="width: 100px; height: auto; padding: 0px 0px 0px 30px; background-color: rgb(238, 238, 238); color: rgb(51, 51, 51); font-weight: 700; font-size: 14px;">新增端口</td> 
                 <td style="height: auto; background-color: rgb(238, 238, 238); text-align: right;"></td> 
                </tr> 
                <tr> 
                 <td style="width:50.0%%;"> 
                  <table cellpadding="0" cellspacing="0" width="auto" style="width:auto;padding:0;border-collapse:collapse;"> 
                   <tbody> 
                    <tr> 
                     <td valign="top" style="padding:0 10.0px 8.0px 30.0px;border:none;font-size:12.0px;color:#333333;vertical-align:top;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;">总数</td> 
                    </tr> 
                    <tr> 
                     <td colspan="2" style="padding:0 0 0 30.0px;font-size:28.0px;color:#333333;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;">%s</td> 
                    </tr> 
                   </tbody> 
                  </table></td> 
                 <td style="width:50.0%%;"></td> 
                </tr> 
               </tbody> 
              </table></td> 
             <td style="width: 30px; height: auto;"></td> 
             <td width="24%%" style="border: 2px solid rgb(238, 238, 238); height: auto;"> 
              <table cellpadding="0" cellspacing="0" style="border-collapse: collapse; border: none; border-spacing: 0px; margin: 0px; width: 100%%; height: auto; padding: 0px;"> 
               <tbody> 
                <tr> 
                 <td style="width: 100px; height: auto; padding: 0px 0px 0px 30px; background-color: rgb(238, 238, 238); color: rgb(51, 51, 51); font-weight: 700; font-size: 14px;">减少IP</td> 
                 <td style="height: auto; background-color: rgb(238, 238, 238); text-align: right;"></td> 
                </tr> 
                <tr> 
                 <td style="width:50.0%%;"> 
                  <table cellpadding="0" cellspacing="0" style="width:auto;padding:0;border-collapse:collapse;"> 
                   <tbody> 
                    <tr> 
                     <td valign="top" style="padding:0 10.0px 8.0px 30.0px;border:none;font-size:12.0px;color:#333333;vertical-align:top;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;">总数</td> 
                    </tr> 
                    <tr> 
                     <td colspan="2" style="padding:0 0 0 30.0px;font-size:28.0px;color:#333333;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;">%s</td> 
                    </tr> 
                   </tbody> 
                  </table></td> 
                 <td style="width:50.0%%;"></td> 
                </tr> 
               </tbody> 
              </table></td> 
            </tr> 
           </tbody> 
          </table></td> 
        </tr> 
        <tr> 
         <td valign="middle" style="padding:10.0px 24.0px;width:100.0%%;"></td> 
        </tr> 
        <tr> 
         <td valign="middle" style="padding:20.0px 24.0px;width:100.0%%;"> 
          <table cellpadding="0" cellspacing="0" style="width:100.0%%;padding:0;color:#ffffff;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;"> 
           <tbody> 
            <tr> 
             <td bgcolor="#0095b3" style="width: 3px; height: auto; padding: 0px; background-color: rgb(20, 158, 204);"></td> 
             <td style="width: 9px; height: auto; padding: 0px;"></td> 
             <td style="line-height: 20px; color: rgb(66, 66, 66); font-family: &quot;Microsoft YaHei&quot;, SimSun, Tahoma, Verdana, Arial, Helvetica, sans-serif; font-weight: 700; font-size: 16px; height: auto;">详情</td> 
            </tr> 
           </tbody> 
          </table></td> 
        </tr> 
        <tr> 
         <td style="padding:0 24.0px;margin:0;"> 
          <table cellpadding="0" cellspacing="0" style="width:100.0%%;border-collapse:collapse;"> 
           <tbody> 
            <tr> 
             <td align="left" colspan="5" valign="middle" style="background:#e6f1ff;font-size:14.0px;padding:0 16.0px;text-align:left;border:1.0px solid #bddbfc;color:#333333;vertical-align:middle;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;">以下为各功能的通知事件，更详细信息请直接登陆网站查看。</td> 
            </tr> 
           </tbody> 
          </table></td> 
        </tr> 
        <tr> 
         <td style="padding:0 24.0px;margin:0;"> 
          <table cellpadding="0" cellspacing="0" style="width:100.0%%;border-collapse:collapse;"> 
           <tbody> 
            <tr> 
             <td style="padding-top:26.0px;"> 
              <table cellpadding="0" cellspacing="0" width="100%%" style="border-collapse:collapse;margin:0;width:100.0%%;padding:0;"> 
               <tbody> 
                <tr> 
                 <th align="left" colspan="7" valign="middle" style="background:#f5f5f5;font-size:16.0px;padding:0 16.0px;text-align:left;border:1.0px solid #eeeeee;color:#333333;vertical-align:middle;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;">新增IP</th> 
                </tr> 
                <tr> 
                 <td valign="middle" width="120" style="height: auto; padding: 0px 20px; color: rgb(102, 102, 102); font-size: 13px; border-bottom: 1px solid rgb(238, 238, 238); border-left: 1px solid rgb(238, 238, 238); font-family: &quot;Microsoft YaHei&quot;, SimSun, Tahoma, Verdana, Arial, Helvetica, sans-serif;">新增IP</td> 
                </tr> 

                 %s 

               </tbody> 
              </table></td> 
            </tr> 
           </tbody> 
          </table></td> 
        </tr> 
        <tr> 
         <td style="padding:0 24.0px;margin:0;"> 
          <table cellpadding="0" cellspacing="0" style="width:100.0%%;border-collapse:collapse;"> 
           <tbody> 
            <tr> 
             <td style="padding-top:26.0px;"> 
              <table cellpadding="0" cellspacing="0" width="100%%" style="border-collapse:collapse;margin:0;width:100.0%%;padding:0;"> 
               <tbody> 
                <tr> 
                 <th align="left" colspan="7" valign="middle" style="background:#f5f5f5;font-size:16.0px;padding:0 16.0px;text-align:left;border:1.0px solid #eeeeee;color:#333333;vertical-align:middle;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;">新增端口</th> 
                </tr> 
                <tr> 
                 <td valign="middle" width="120" style="height: auto; padding: 0px 20px; color: rgb(102, 102, 102); font-size: 13px; border-bottom: 1px solid rgb(238, 238, 238); border-left: 1px solid rgb(238, 238, 238); font-family: &quot;Microsoft YaHei&quot;, SimSun, Tahoma, Verdana, Arial, Helvetica, sans-serif;">新增端口</td> 
                </tr> 

                %s

               </tbody> 
              </table></td> 
            </tr> 
           </tbody> 
          </table></td> 
        </tr> 
        <tr> 
         <td style="padding:0 24.0px;margin:0;"> 
          <table cellpadding="0" cellspacing="0" style="width:100.0%%;border-collapse:collapse;"> 
           <tbody> 
            <tr> 
             <td style="padding-top:26.0px;"> 
              <table cellpadding="0" cellspacing="0" width="100%%" style="border-collapse:collapse;margin:0;width:100.0%%;padding:0;"> 
               <tbody> 
                <tr> 
                 <th align="left" colspan="7" valign="middle" style="background:#f5f5f5;font-size:16.0px;padding:0 16.0px;text-align:left;border:1.0px solid #eeeeee;color:#333333;vertical-align:middle;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;">减少IP</th> 
                </tr> 
                <tr> 
                 <td valign="middle" width="120" style="height: auto; padding: 0px 20px; color: rgb(102, 102, 102); font-size: 13px; border-bottom: 1px solid rgb(238, 238, 238); border-left: 1px solid rgb(238, 238, 238); font-family: &quot;Microsoft YaHei&quot;, SimSun, Tahoma, Verdana, Arial, Helvetica, sans-serif;">减少IP</td> 
                </tr> 

                 %s 

               </tbody> 
              </table></td> 
            </tr> 
           </tbody> 
          </table></td> 
        </tr> 
       </tbody> 
      </table>  

    """ % (scan_time, add_ips_count, add_ports_count, del_ips_count, add_ips_html, add_ports_html, del_ips_html)
    return html


def format_monitor_html(scan_time="", ips_count=0, ips=set()):
    # 邮件正文

    ips_html = ""

    for ip in ips:
        ips_html += """
         <tr>
        <td style="height: auto; padding: 0px 20px; color: rgb(51, 51, 51); font-size: 13px; border-bottom: 1px solid rgb(238, 238, 238); border-left: 1px solid rgb(238, 238, 238); font-family: &quot;Microsoft YaHei&quot;, SimSun, Tahoma, Verdana, Arial, Helvetica, sans-serif;">%s</td> 
       </tr> """ % ip

    html = """
    <table cellpadding="0" cellspacing="0" style="margin: 0px; padding: 0px; width: 1000px;" _ow="1280px"> 
       <tbody> 
        <tr style="padding:0;"> 
         <td valign="middle" style="padding: 0px 24px; height: auto; width: 100%%; background-color: rgb(20, 158, 204);"> 
          <table bgcolor="#149ECC" cellpadding="0" cellspacing="0" style="padding:0;color:#ffffff;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;"> 
           <tbody> 
            <tr> 
             <td valign="middle" style="height: auto; color: rgb(255, 255, 255); line-height: 20px; font-size: 20px; vertical-align: middle; border: none; padding: 0px; margin: 0px; font-family: &quot;Microsoft YaHei&quot;, SimSun, Tahoma, Verdana, Arial, Helvetica, sans-serif;">监控端口开放情况结果</td> 
             <td style="width: 9px; height: auto; padding: 0px;"></td> 
             <td style="width: 3px; height: auto; padding: 0px; color: rgb(255, 255, 255);">|</td> 
             <td style="width: 9px; height: auto; padding: 0px;"></td> 
             <td style="height: auto; color: rgb(255, 255, 255); line-height: 21px; font-size: 12px; vertical-align: middle; border: none; padding: 0px; margin: 0px; font-family: &quot;Microsoft YaHei&quot;, SimSun, Tahoma, Verdana, Arial, Helvetica, sans-serif;"><span>%s</span></td> 
            </tr> 
           </tbody> 
          </table></td> 
        </tr> 
        <tr> 
         <td valign="middle" style="padding:20.0px 24.0px;width:100.0%%;"> 
          <table cellpadding="0" cellspacing="0" style="width:100.0%%;padding:0;color:#ffffff;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;"> 
           <tbody> 
            <tr> 
             <td bgcolor="#0095b3" style="width: 3px; height: auto; padding: 0px; background-color: rgb(20, 158, 204);"></td> 
             <td style="width: 9px; height: auto; padding: 0px;"></td> 
             <td style="line-height: 20px; color: rgb(66, 66, 66); font-family: &quot;Microsoft YaHei&quot;, SimSun, Tahoma, Verdana, Arial, Helvetica, sans-serif; font-weight: 700; font-size: 16px; height: auto;">结果概述</td> 
            </tr> 
           </tbody> 
          </table></td> 
        </tr> 
        <tr> 
         <td valign="middle" style="padding:0 24.0px 10.0px;width:100.0%%;"> 
          <table cellpadding="0" cellspacing="0" style="width:100.0%%;padding:0;color:#ffffff;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;"> 
           <tbody> 
            <tr> 
             <td width="24%%" style="border: 2px solid rgb(238, 238, 238); height: auto;"> 
              <table cellpadding="0" cellspacing="0" style="border-collapse: collapse; border: none; border-spacing: 0px; margin: 0px; width: 100%%; height: auto; padding: 0px;"> 
               <tbody> 
                <tr> 
                 <td style="width: 100px; height: auto; padding: 0px 0px 0px 30px; background-color: rgb(238, 238, 238); color: rgb(51, 51, 51); font-weight: 700; font-size: 14px;">端口开放数</td> 
                 <td style="height: auto; background-color: rgb(238, 238, 238); text-align: right;"></td> 
                </tr> 
                <tr> 
                 <td style="width:50.0%%;"> 
                  <table cellpadding="0" cellspacing="0" style="width:auto;padding:0;border-collapse:collapse;"> 
                   <tbody> 
                    <tr> 
                     <td valign="top" style="padding:0 10.0px 8.0px 30.0px;border:none;font-size:12.0px;color:#333333;vertical-align:top;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;">总数</td> 
                    </tr> 
                    <tr> 
                     <td colspan="2" style="padding:0 0 0 30.0px;font-size:28.0px;color:#333333;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;">%s</td> 
                    </tr> 
                   </tbody> 
                  </table></td> 
                 <td style="width:50.0%%;"></td> 
                </tr> 
               </tbody> 
              </table></td> 
             <td style="width: 30px; height: auto;"></td> 

            </tr> 
           </tbody> 
          </table></td> 
        </tr> 
        <tr> 
         <td valign="middle" style="padding:10.0px 24.0px;width:100.0%%;"></td> 
        </tr> 
        <tr> 
         <td valign="middle" style="padding:20.0px 24.0px;width:100.0%%;"> 
          <table cellpadding="0" cellspacing="0" style="width:100.0%%;padding:0;color:#ffffff;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;"> 
           <tbody> 
            <tr> 
             <td bgcolor="#0095b3" style="width: 3px; height: auto; padding: 0px; background-color: rgb(20, 158, 204);"></td> 
             <td style="width: 9px; height: auto; padding: 0px;"></td> 
             <td style="line-height: 20px; color: rgb(66, 66, 66); font-family: &quot;Microsoft YaHei&quot;, SimSun, Tahoma, Verdana, Arial, Helvetica, sans-serif; font-weight: 700; font-size: 16px; height: auto;">详情</td> 
            </tr> 
           </tbody> 
          </table></td> 
        </tr> 
        <tr> 
         <td style="padding:0 24.0px;margin:0;"> 
          <table cellpadding="0" cellspacing="0" style="width:100.0%%;border-collapse:collapse;"> 
           <tbody> 
            <tr> 
             <td align="left" colspan="5" valign="middle" style="background:#e6f1ff;font-size:14.0px;padding:0 16.0px;text-align:left;border:1.0px solid #bddbfc;color:#333333;vertical-align:middle;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;">以下为各功能的通知事件，更详细信息请直接登陆网站查看。</td> 
            </tr> 
           </tbody> 
          </table></td> 
        </tr> 
        <tr> 
         <td style="padding:0 24.0px;margin:0;"> 
          <table cellpadding="0" cellspacing="0" style="width:100.0%%;border-collapse:collapse;"> 
           <tbody> 
            <tr> 
             <td style="padding-top:26.0px;"> 
              <table cellpadding="0" cellspacing="0" width="100%%" style="border-collapse:collapse;margin:0;width:100.0%%;padding:0;"> 
               <tbody> 
                <tr> 
                 <th align="left" colspan="7" valign="middle" style="background:#f5f5f5;font-size:16.0px;padding:0 16.0px;text-align:left;border:1.0px solid #eeeeee;color:#333333;vertical-align:middle;font-family:Microsoft YaHei,SimSun,Tahoma,Verdana,Arial,Helvetica,sans-serif;">IP</th> 
                </tr> 


                 %s 

               </tbody> 
              </table></td> 
            </tr> 
           </tbody> 
          </table></td> 
        </tr> 
        
       </tbody> 
      </table>  

    """ % (scan_time, ips_count, ips_html)
    return html


if __name__ == '__main__':
    task_process()
