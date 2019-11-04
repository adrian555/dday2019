from pyspark.sql import SparkSession
from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.sql import SQLContext

from subprocess import check_output
ip = check_output(['hostname', '-i']).decode().rstrip()

import os
app = os.getenv("APP_NAME", "demo")
master = os.getenv("SPARK_MASTER", "local[*]")

spark = SparkSession.builder.master(master).appName(app).config("spark.driver.host", ip).getOrCreate()
sc = spark.sparkContext
sql = SQLContext(sc)

#import random
#num_samples = 100000000

#def inside(p):
#  x, y = random.random(), random.random()
#  return x*x + y*y < 1

#count = sc.parallelize(range(0, num_samples), 4).filter(inside).count()

#pi = 4 * count / num_samples
#print(pi)

import pandas as pd
df = spark.createDataFrame(pd.read_csv("http://oc-minio-default.apps.ddoc.os.fyre.ibm.com/test/sample_data.csv"))

print(df.collect())

spark.stop()
