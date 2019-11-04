From python:3.6-slim

RUN mkdir -p /usr/share/man/man1 && \
    mkdir -p /opt/app && \
    echo "deb http://ftp.us.debian.org/debian sid main" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y openjdk-8-jdk && \
    pip install pyspark pandas minio && \
    rm -rf /root/.cache

COPY pipeline.py /opt/app

#CMD ["sh", "-c", "sleep 10d"]

CMD ["sh", "-c", "python /opt/app/pipeline.py ${APP_OPS}"]