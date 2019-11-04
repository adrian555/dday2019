#
# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

FROM openjdk:8-alpine

ARG spark_jars=jars
ARG img_path=kubernetes/dockerfiles
ARG k8s_tests=kubernetes/tests

# Before building the docker image, first build and make a Spark distribution following
# the instructions in http://spark.apache.org/docs/latest/building-spark.html.
# If this docker file is being used in the context of building your images from a Spark
# distribution, the docker build command should be invoked from the top level directory
# of the Spark distribution. E.g.:
# docker build -t spark:latest -f kubernetes/dockerfiles/spark/Dockerfile .

ENV NFS_SERVER none
RUN set -ex && \
    apk upgrade --no-cache && \
    ln -s /lib /lib64 && \
    apk add --no-cache bash tini libc6-compat linux-pam nss curl python3 py3-pip && \
    pip3 install pyspark && \
    ln -s /usr/bin/python3 /usr/bin/python && \
    mkdir -p /opt/spark && \
    mkdir -p /opt/spark/conf && \
    mkdir -p /opt/spark/work-dir && \
    touch /opt/spark/RELEASE && \
    rm /bin/sh && \
    ln -sv /bin/bash /bin/sh && \
    echo "auth required pam_wheel.so use_uid" >> /etc/pam.d/su && \
    chgrp root /etc/passwd && chmod ug+rw /etc/passwd && \
    rm -rf /root/.cache

COPY ${spark_jars} /opt/spark/jars
COPY bin /opt/spark/bin
COPY sbin /opt/spark/sbin
COPY conf /opt/spark/conf
COPY spark-env.sh /opt/spark/conf
RUN chmod +x /opt/spark/conf/spark-env.sh
COPY ${img_path}/spark/entrypoint.sh /opt/
COPY examples /opt/spark/examples
COPY ${k8s_tests} /opt/spark/tests
COPY data /opt/spark/data

ENV SPARK_HOME /opt/spark

ENV SPARK_MASTER_PORT 7077
ENV SPARK_MASTER_WEBUI_PORT 8080
ENV SPARK_MASTER_LOG /opt/spark/logs

ENV SPARK_NO_DAEMONIZE yes

ENV SPARK_WORKER_CORES=1
ENV SPARK_WORKER_MEMORY=4G

ENV SPARK_MASTER "spark://spark-master:7077"
ENV SPARK_WORKER_WEBUI_PORT 8081

EXPOSE ${SPARK_MASTER_PORT}
EXPOSE ${SPARK_MASTER_WEBUI_PORT}
EXPOSE ${SPARK_WORKER_WEBUI_PORT}

WORKDIR /opt/spark/work-dir

RUN wget https://gist.github.com/ashsmith/55098099d2a5b5dfed9935dd4488abd6/raw/9113834d220fca40ed69e53c198a8891a4357d8e/ps_opt_p_enabled_for_alpine.sh \ 
  && mv ps_opt_p_enabled_for_alpine.sh /usr/local/bin/ps \
  && chmod +x /usr/local/bin/ps

RUN wget https://jdbc.postgresql.org/download/postgresql-42.2.8.jar \
  && mv postgresql-42.2.8.jar /opt/spark/jars

ENV RUN_SPARK_AS master

CMD ["bash", "/opt/spark/sbin/run.sh"]