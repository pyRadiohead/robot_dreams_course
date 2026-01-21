FROM python:3.12.9-bullseye AS spark-base

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      sudo \
      curl \
      vim \
      unzip \
      rsync \
      openjdk-11-jdk \
      build-essential \
      software-properties-common \
      ssh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

## Download spark and hadoop dependencies and install

# ENV variables
ENV SPARK_VERSION=3.5.5

ENV SPARK_HOME="/opt/spark"
ENV HADOOP_HOME="/opt/hadoop"
# ENV JAVA_HOME="/usr/lib/jvm/java-11-openjdk-amd64"
# ENV PATH $JAVA_HOME/bin:$PATH
# ENV IJAVA_CLASSPATH="/opt/spark/jars/*"

ENV SPARK_MASTER_PORT=7077
ENV SPARK_MASTER_HOST=spark-master
ENV SPARK_MASTER="spark://$SPARK_MASTER_HOST:$SPARK_MASTER_PORT"

ENV PYTHONPATH=$SPARK_HOME/python/:$PYTHONPATH
ENV PYSPARK_PYTHON=python3

RUN mkdir -p ${HADOOP_HOME} && mkdir -p ${SPARK_HOME}
WORKDIR ${SPARK_HOME}

# Download spark
# see resources: https://archive.apache.org/dist/spark/spark-3.5.5/
# filename: spark-3.5.5-bin-hadoop3.tgz 
RUN mkdir -p ${SPARK_HOME} \
    && curl https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop3.tgz -o spark-${SPARK_VERSION}-bin-hadoop3.tgz \
    && tar xvzf spark-${SPARK_VERSION}-bin-hadoop3.tgz --directory ${SPARK_HOME} --strip-components 1 \
    && rm -rf spark-${SPARK_VERSION}-bin-hadoop3.tgz

# Add spark binaries to shell and enable execution
RUN chmod u+x /opt/spark/sbin/* && \
    chmod u+x /opt/spark/bin/*
ENV PATH="$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin"

# Add a spark config for all nodes
COPY ./spark-defaults.conf "$SPARK_HOME/conf/"
COPY ./entrypoint.sh "$SPARK_HOME/entrypoint.sh"

# Set proper permissions for the entrypoint script
RUN chmod +x "$SPARK_HOME/entrypoint.sh"

FROM spark-base AS jupyter-base

COPY requirements.txt .
RUN pip3 install -r requirements.txt

EXPOSE 8889
WORKDIR /opt/workspace
ENV PYSPARK_DRIVER_PYTHON=jupyter

ENV PYSPARK_DRIVER_PYTHON_OPTS="lab --no-browser --allow-root --ip=0.0.0.0 --port=8889 --NotebookApp.token="

ENTRYPOINT ["/opt/spark/entrypoint.sh"]

CMD ["bash"]