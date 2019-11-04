From python:3.6-slim

RUN mkdir -p /usr/share/man/man1 && \
    mkdir -p /opt/app && \
    echo "deb http://ftp.us.debian.org/debian sid main" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y openjdk-8-jdk wget && \
    pip install pyspark pandas minio pyyaml && \
    wget https://storage.googleapis.com/kubernetes-release/release/v1.13.4/bin/linux/amd64/kubectl -O /opt/app/kubectl && \
    chmod +x /opt/app/kubectl && \
    rm -rf /root/.cache

COPY pipeline.py /opt/app
COPY processing_cr.yaml /opt/app
COPY training_cr.yaml /opt/app
COPY scoring_cr.yaml /opt/app
COPY deploy.py /opt/app