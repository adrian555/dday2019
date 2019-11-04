from pyspark.sql import SparkSession
from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.sql import SQLContext

spark = SparkSession.builder.master("spark://localhost:31505").appName("demo").config("spark.driver.host", "9.160.43.207").getOrCreate()
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

df.collect()

spark.stop()


from pyspark.sql import SparkSession
from pyspark import SparkContext
from pyspark import SparkConf
from pyspark.sql import SQLContext

#spark = SparkSession.builder.master("spark://master0.ddoc.os.fyre.ibm.com:31505").appName("demo").config("spark.driver.host", "10.16.3.222").config("spark.driver.bindAddress", "0.0.0.0").config("spark.driver.blockManagerPort", "51500").config("spark.driver.port", "41007").getOrCreate()
spark = SparkSession.builder.master("spark://master0.ddoc.os.fyre.ibm.com:31505").appName("demo").config("spark.driver.host", "10.88.0.4").getOrCreate()
#sc = spark.sparkContext
#sql = SQLContext(sc)

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