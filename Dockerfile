FROM ubuntu:14.04
MAINTAINER zj1244
ENV LC_ALL C.UTF-8
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN set -x \
    && apt-get update \
    && apt-get install nmap python-pip python-dev -y \
    && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /opt/beholder_scanner
COPY . /opt/beholder_scanner

RUN set -x \
    && pip install -r /opt/beholder_scanner/requirements.txt \
    && cp /opt/beholder_scanner/scanner/config.py.sample /opt/beholder_scanner/scanner/config.py

WORKDIR /opt/beholder_scanner
ENTRYPOINT ["python","main.py"]
CMD ["/usr/bin/tail", "-f", "/dev/null"]