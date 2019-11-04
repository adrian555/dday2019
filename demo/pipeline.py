import os
from pyspark.sql import SparkSession
from pyspark.ml import Pipeline
from pyspark.sql.functions import mean,col,split, col, regexp_extract, when, lit
from pyspark.ml.feature import StringIndexer
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.feature import QuantileDiscretizer
from pyspark.ml.classification import GBTClassifier
from pyspark.ml.classification import GBTClassificationModel
from minio import Minio
from minio.error import (ResponseError)

minioClient = Minio('oc-minio-default.apps.ddoc.os.fyre.ibm.com',
                    access_key='minio',
                    secret_key='minio123',
                    secure=False)

def get_mean_age(mean_ages, x):
    return round(mean_ages.filter(mean_ages.Initial == x).select('avg(Age)').collect()[0][0])

def ingestion():
  parts = []
  for dirpath, dirs, files in os.walk("/pfs/titanic"):
    for file in files:
      if file.startswith('part'):
        parts.append(file)

  concat = ''.join([open(os.path.join("/pfs/titanic", f)).read() for f in parts])
  concat = "PassengerId,Survived,Pclass,Name,Sex,Age,SibSp,Parch,Ticket,Fare,Cabin,Embarked\n" + concat

  f = open('/pfs/out/data.csv', 'w')
  f.write(concat)
  f.close()

  try:
      minioClient.fput_object('titanic', 'data.csv', '/pfs/out/data.csv')
  except ResponseError as err:
      print(err)

def processing():
  if os.path.exists("/mnt/pfs/processing"):
    os.remove("/mnt/pfs/processing")

  try:
      print(minioClient.fget_object('titanic', 'data.csv', '/mnt/pfs/data.csv'))
  except ResponseError as err:
      print(err)

  from subprocess import check_output
  ip = check_output(['hostname', '-i']).decode().rstrip()

  spark = SparkSession.builder \
      .master(os.getenv("SPARK_MASTER", "local[*]")) \
      .appName(os.getenv("APP_NAME", "demo")) \
      .config('spark.sql.codegen.wholeStage', 'false') \
      .config("spark.driver.host", ip) \
      .getOrCreate()

  df = spark.read.csv('/mnt/pfs/data.csv', header=True)

  df = df.select(col("Survived").cast("int"),col("PassengerId").cast("int"),col("Name"),col("Parch").cast("int"),col("Sex"),col("Embarked"),col("Pclass").cast("int"),col("Age").cast("double"),col("SibSp").cast("int"),col("Fare").cast("double"))

  df = df.withColumn("Initial",regexp_extract(col("Name"),"([A-Za-z]+)\.",1))
  df = df.replace(['Mlle','Mme', 'Ms', 'Dr','Major','Lady','Countess','Jonkheer','Col','Rev','Capt','Sir','Don'],
                ['Miss','Miss','Miss','Mr','Mr',  'Mrs',  'Mrs',  'Other',  'Other','Other','Mr','Mr','Mr'])
  mean_ages = df.groupby('Initial').avg('Age')
  df = df.withColumn("Age",when(df["Age"].isNull(), get_mean_age(mean_ages, df["Initial"])).otherwise(df["Age"]))
  df = df.na.fill({"Embarked" : 'S'})
  df = df.withColumn("Family_Size",col('SibSp')+col('Parch'))
  df = df.withColumn('Alone',lit(0))
  df = df.withColumn("Alone",when(df["Family_Size"] == 0, 1).otherwise(df["Alone"]))

  indexers = [StringIndexer(inputCol=column, outputCol=column+"_index").fit(df) for column in ["Sex","Embarked","Initial"]]
  pipeline = Pipeline(stages=indexers)
  df = pipeline.fit(df).transform(df)
  df = df.drop("PassengerId","Name","Embarked","Sex","Initial")

  feature = VectorAssembler(inputCols=df.columns[1:],outputCol="features")
  feature_vector= feature.transform(df)

  (trainingData, testData) = feature_vector.randomSplit([0.8, 0.2],seed = 11)
  trainingData.write.format("parquet").mode("overwrite").save("/mnt/pfs/train.parquet")
  testData.write.format("parquet").mode("overwrite").save("/mnt/pfs/test.parquet")

  f = open('/mnt/pfs/processing', 'w')
  f.write("Done")
  f.close()

  try:
      minioClient.fput_object('titanic', 'processing', '/mnt/pfs/processing')
  except ResponseError as err:
      print(err)

  spark.stop()

def training():
  if os.path.exists("/mnt/pfs/training"):
    os.remove("/mnt/pfs/training")

  from subprocess import check_output
  ip = check_output(['hostname', '-i']).decode().rstrip()

  spark = SparkSession.builder \
      .master(os.getenv("SPARK_MASTER", "local[*]")) \
      .appName(os.getenv("APP_NAME", "demo")) \
      .config('spark.sql.codegen.wholeStage', 'false') \
      .config("spark.driver.host", ip) \
      .getOrCreate()

  trainingData = spark.read.parquet("/mnt/pfs/train.parquet")
  gbt = GBTClassifier(labelCol="Survived", featuresCol="features",maxIter=int(os.getenv('APP_MAX_ITER', '10')), seed=20, maxDepth=4)
  gbt_model = gbt.fit(trainingData)
  gbt_model.write().overwrite().save("/mnt/pfs/gbt")

  f = open('/mnt/pfs/training', 'w')
  f.write("Done")
  f.close()

  try:
      minioClient.fput_object('titanic', 'training', '/mnt/pfs/training')
  except ResponseError as err:
      print(err)

  spark.stop()

def scoring():
  if os.path.exists("/mnt/pfs/scoring"):
    os.remove("/mnt/pfs/scoring")

  from subprocess import check_output
  ip = check_output(['hostname', '-i']).decode().rstrip()

  spark = SparkSession.builder \
      .master(os.getenv("SPARK_MASTER", "local[*]")) \
      .appName(os.getenv("APP_NAME", "demo")) \
      .config('spark.sql.codegen.wholeStage', 'false') \
      .config("spark.driver.host", ip) \
      .getOrCreate()

  gbt_model = GBTClassificationModel.load("/mnt/pfs/gbt")
  testData = spark.read.parquet("/mnt/pfs/test.parquet")
  evaluator = MulticlassClassificationEvaluator(labelCol="Survived", predictionCol="prediction", metricName="accuracy")
  gbt_prediction = gbt_model.transform(testData)
  gbt_accuracy = evaluator.evaluate(gbt_prediction)
  print("Accuracy of Gradient-boosted tree classifier is = %g"% (gbt_accuracy))
  print("Test Error of Gradient-boosted tree classifier %g"% (1.0 - gbt_accuracy))

  f = open('/mnt/pfs/scoring', 'w')
  f.write("Accuracy of Gradient-boosted tree classifier is = %g"% (gbt_accuracy))
  f.write("\n")
  f.write("Test Error of Gradient-boosted tree classifier %g"% (1.0 - gbt_accuracy))
  f.close()

  try:
      minioClient.fput_object('titanic', 'scoring', '/mnt/pfs/scoring')
  except ResponseError as err:
      print(err)

  spark.stop()

if __name__ == "__main__":
  app_ops = os.getenv("APP_OPS")
  if app_ops == 'processing':
    processing()
  elif app_ops == 'training':
    training()
  elif app_ops == 'scoring':
    scoring()
  else:
    ingestion()
  
  import time
  time.sleep(360000)
