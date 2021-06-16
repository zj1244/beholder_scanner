FROM ubuntu:14.04
MAINTAINER zj1244
ENV LC_ALL C.UTF-8
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN set -x \
    && apt-get update \
    && apt-get install curl python-pip python-dev flex bison libssl-dev libpcap-dev -y \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /opt/beholder_scanner

COPY . /opt/beholder_scanner

RUN set -x \
    && pip install -r /opt/beholder_scanner/requirements.txt \
    && cp /opt/beholder_scanner/scanner/config.py.sample /opt/beholder_scanner/scanner/config.py \
    && cp /opt/beholder_scanner/scanner/thirdparty/http-check.nse /usr/local/share/nmap/scripts/http-check.nse \
    && curl -fL -o /tmp/nmap.tar.bz2 \
         https://nmap.org/dist/nmap-7.80.tar.bz2 \
    && tar -xjf /tmp/nmap.tar.bz2 -C /tmp \
    && cd /tmp/nmap* \
    && ./configure \
    && make \
    && make install \
    && rm -rf /var/lib/apt/lists/* \
           /tmp/nmap*

WORKDIR /opt/beholder_scanner
CMD ["/bin/bash","-c","set -e && python main.py"]