#!/usr/bin/env python
# coding: utf-8
import subprocess
import sys
import re
import os
import shlex
import json
from threading import Timer
from scanner.thirdparty import nmap

PORTS = "1-65535"
TIMEOUT = 10


class Masscan(object):
    def __init__(self, masscan_search_path=(
            'masscan', '/usr/bin/masscan', '/usr/local/bin/masscan', '/sw/bin/masscan', '/opt/local/bin/masscan')):
        self._masscan_path = ''  # masscan path
        self._scan_result = []
        self._masscan_version_number = 0  # masscan version number
        self._masscan_subversion_number = 0  # masscan subversion number
        self._masscan_revised_number = 0  # masscan revised number
        self._masscan_last_output = ''  # last full ascii masscan output
        self._args = ''
        self._scaninfo = {}
        is_masscan_found = False  # true if we have found masscan

        # launch 'masscan -V', we wait after
        # 'Masscan version 1.0.3 ( https://github.com/robertdavidgraham/masscan )'
        # This is for Mac OSX. When idle3 is launched from the finder, PATH is not set so masscan was not found
        for masscan_path in masscan_search_path:
            try:
                if sys.platform.startswith('freebsd') \
                        or sys.platform.startswith('linux') \
                        or sys.platform.startswith('darwin'):
                    p = subprocess.Popen([masscan_path, '-V'],
                                         bufsize=10000,
                                         stdout=subprocess.PIPE,
                                         close_fds=True)
                else:
                    p = subprocess.Popen([masscan_path, '-V'],
                                         bufsize=10000,
                                         stdout=subprocess.PIPE)

            except OSError:
                pass
            else:
                self._masscan_path = masscan_path  # save path
                is_masscan_found = True
                break
        else:
            raise PortScannerError(
                'masscan program was not found in path. PATH is : {0}'.format(os.getenv('PATH'))
            )

        if not is_masscan_found:
            raise PortScannerError('masscan program was not found in path')

    def scan(self, hosts='127.0.0.1', ports=PORTS, arguments='', sudo=False):
        if sys.version_info[0] == 2:
            assert type(hosts) in (str, unicode), 'Wrong type for [hosts], should be a string [was {0}]'.format(
                type(hosts))  # noqa
            assert type(ports) in (
                str, unicode, type(None)), 'Wrong type for [ports], should be a string [was {0}]'.format(
                type(ports))  # noqa
            assert type(arguments) in (str, unicode), 'Wrong type for [arguments], should be a string [was {0}]'.format(
                type(arguments))  # noqa
        else:
            assert type(hosts) is str, 'Wrong type for [hosts], should be a string [was {0}]'.format(
                type(hosts))  # noqa
            assert type(ports) in (str, type(None)), 'Wrong type for [ports], should be a string [was {0}]'.format(
                type(ports))  # noqa
            assert type(arguments) is str, 'Wrong type for [arguments], should be a string [was {0}]'.format(
                type(arguments))  # noqa

        h_args = shlex.split(hosts)
        f_args = shlex.split(arguments)

        # Launch scan
        args = [self._masscan_path, '-oJ', '-'] + h_args + ['-p', ports] * (ports is not None) + f_args

        # logger.debug('Scan parameters: "' + ' '.join(args) + '"')
        self._args = ' '.join(args)

        if sudo:
            args = ['sudo'] + args

        p = subprocess.Popen(args,
                             bufsize=100000,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE
                             )

        # wait until finished
        # get output
        self._masscan_last_output, masscan_err = p.communicate()
        self._masscan_last_output = bytes.decode(self._masscan_last_output)
        masscan_err = bytes.decode(masscan_err)

        if len(self._masscan_last_output) > 0:
            self._scan_result = json.loads(self._masscan_last_output)

        return self._scan_result

    def scan_result(self):
        return self._scan_result


class PortScannerError(Exception):
    """
    Exception error class for PortScanner class
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

    def __repr__(self):
        return 'PortScannerError exception {0}'.format(self.value)


class Nmap(nmap.PortScanner):
    def scan_result(self):
        scan_result_list = []

        for k_ip, p_port in self._scan_result.get('scan', {}).items():
            if 'tcp' in p_port.keys():
                for k, v in p_port['tcp'].items():

                    if p_port['tcp'][k]['state'] == "open":
                        result_dict = {}
                        result_dict['ip'] = k_ip
                        result_dict['port'] = k

                        result_dict['service'] ='http' if v['script']['http-check'].strip() else v['name']
                        # result_dict['status'] = 'open'
                        result_dict['version_info'] = "%s %s (%s)".strip() % (
                            v["product"], v["version"], v['extrainfo']) if v[
                                                                               'extrainfo'].strip() != "" else "%s %s".strip() % (
                            v["product"], v["version"])
                        if 'script' in p_port['tcp'][k].keys():
                            result_dict['script'] = {}
                            for kk, vv in p_port['tcp'][k]['script'].items():
                                result_dict['script'][kk] = vv
                        scan_result_list.append(result_dict)
                    else:
                        pass

        return scan_result_list




    def scan(self, hosts='127.0.0.1', ports=None, arguments='-sV', sudo=False, timeout=60 * 5):
        def kill(p):
            p.kill()
            print('scanning timeout:ip={0},port={1},arguments={2},timeout={3}'.format(hosts,ports,arguments,timeout))

        if sys.version_info[0] == 2:
            assert type(hosts) in (str, unicode), 'Wrong type for [hosts], should be a string [was {0}]'.format(
                type(hosts))  # noqa
            assert type(ports) in (
                str, unicode, type(None)), 'Wrong type for [ports], should be a string [was {0}]'.format(
                type(ports))  # noqa
            assert type(arguments) in (str, unicode), 'Wrong type for [arguments], should be a string [was {0}]'.format(
                type(arguments))  # noqa
        else:
            assert type(hosts) is str, 'Wrong type for [hosts], should be a string [was {0}]'.format(
                type(hosts))  # noqa
            assert type(ports) in (str, type(None)), 'Wrong type for [ports], should be a string [was {0}]'.format(
                type(ports))  # noqa
            assert type(arguments) is str, 'Wrong type for [arguments], should be a string [was {0}]'.format(
                type(arguments))  # noqa

        for redirecting_output in ['-oX', '-oA']:
            assert redirecting_output not in arguments, 'Xml output can\'t be redirected from command line.\nYou can access it after a scan using:\nnmap.nm.get_nmap_last_output()'  # noqa

        h_args = shlex.split(hosts)
        f_args = shlex.split(arguments)

        # Launch scan
        args = [self._nmap_path, '-oX', '-'] + h_args + ['-p', ports] * (ports is not None) + f_args
        if sudo:
            args = ['sudo'] + args

        # kill = lambda process: process.kill()

        p = subprocess.Popen(args, bufsize=100000,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)

        my_timer = Timer(timeout, kill, [p])
        # try:
        #     my_timer.start()
        #     stdout, stderr = p.communicate()
        # finally:
        #     my_timer.cancel()

        # wait until finished
        # get output
        try:
            my_timer.start()
            (self._nmap_last_output, nmap_err) = p.communicate()
        finally:
            my_timer.cancel()

        self._nmap_last_output = bytes.decode(self._nmap_last_output)
        nmap_err = bytes.decode(nmap_err)

        nmap_err_keep_trace = []
        nmap_warn_keep_trace = []
        if len(nmap_err) > 0:
            regex_warning = re.compile('^Warning: .*', re.IGNORECASE)
            for line in nmap_err.split(os.linesep):
                if len(line) > 0:
                    rgw = regex_warning.search(line)
                    if rgw is not None:
                        # sys.stderr.write(line+os.linesep)
                        nmap_warn_keep_trace.append(line + os.linesep)
                    else:
                        # raise PortScannerError(nmap_err)
                        nmap_err_keep_trace.append(nmap_err)

        return self.analyse_nmap_xml_scan(
            nmap_xml_output=self._nmap_last_output,
            nmap_err=nmap_err,
            nmap_err_keep_trace=nmap_err_keep_trace,
            nmap_warn_keep_trace=nmap_warn_keep_trace
        )


if __name__ == "__main__":
    port = "9090"
    nm = Nmap()
    x = nm.scan(hosts='127.0.0.1', ports=port,arguments='-sV -T4 --version-intensity 4 --script=http-check', timeout=80)
    print nm.scan_result()
