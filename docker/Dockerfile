FROM ubuntu:xenial

# root is the home directory
WORKDIR /root

ADD simple_example.py /root/simple_example.py

# set up the system tools including conda
RUN \
    rm /bin/sh && ln -s /bin/bash /bin/sh && \
    apt-get update && \
    apt-get install -y vim && \
    apt-get install -y git  && \
    apt-get install -y wget && \
    apt-get install -y curl && \
    apt-get install -y graphviz && \
    apt-get install -y python-dev

RUN \
    curl -sS https://bootstrap.pypa.io/get-pip.py | python

RUN \
    pip install git+https://github.com/robdmc/consecution.git
