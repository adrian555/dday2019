def get_mean_age(x):
    return round(mean_ages.filter(mean_ages.Initial == x).select('avg(Age)').collect()[0][0])

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

def processing():
  parts = ["header"]
  for dirpath, dirs, files in os.walk("/pfs/titanic"):
    for file in files:
      if file.startswith('part'):
        parts.append(file)

  concat = ''.join([open(os.path.join("/pfs/titanic", f)).read() for f in parts])
  f = open('/mnt/pfs/data.csv', 'w')
  f.write(concat)
  f.close()


  spark = SparkSession.builder \
      .master(os.getenv("SPARK_MASTER", "local[*]")) \
      .appName(os.getenv("APP_NAME", "demo")) \
      .config('spark.sql.codegen.wholeStage', 'false') \
      .getOrCreate()

  df = spark.read.csv('/mnt/pfs/data.csv', header=True)

  df = df.select(col("Survived").cast("int"),col("PassengerId").cast("int"),col("Name"),col("Parch").cast("int"),col("Sex"),col("Embarked"),col("Pclass").cast("int"),col("Age").cast("double"),col("SibSp").cast("int"),col("Fare").cast("double"))

  df = df.withColumn("Initial",regexp_extract(col("Name"),"([A-Za-z]+)\.",1))
  df = df.replace(['Mlle','Mme', 'Ms', 'Dr','Major','Lady','Countess','Jonkheer','Col','Rev','Capt','Sir','Don'],
                ['Miss','Miss','Miss','Mr','Mr',  'Mrs',  'Mrs',  'Other',  'Other','Other','Mr','Mr','Mr'])
  mean_ages = df.groupby('Initial').avg('Age')
  df = df.withColumn("Age",when(df["Age"].isNull(), get_mean_age(df["Initial"])).otherwise(df["Age"]))
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

  spark.stop()

def training():
  spark = SparkSession.builder \
    .master(os.getenv("SPARK_MASTER", "local[*]")) \
    .appName(os.getenv("APP_NAME", "demo")) \
    .config('spark.sql.codegen.wholeStage', 'false') \
    .getOrCreate()

  trainingData = spark.read.parquet("/mnt/pfs/train.parquet")
  gbt = GBTClassifier(labelCol="Survived", featuresCol="features",maxIter=int(os.getenv('APP_MAX_ITER', '10')), seed=20, maxDepth=4)
  gbt_model = gbt.fit(trainingData)
  gbt_model.write().overwrite().save("/mnt/pfs/gbt")

  spark.stop()

def scoring():
  spark = SparkSession.builder \
    .master(os.getenv("SPARK_MASTER", "local[*]")) \
    .appName(os.getenv("APP_NAME", "demo")) \
    .config('spark.sql.codegen.wholeStage', 'false') \
    .getOrCreate()

  gbt_model = GBTClassificationModel.load("/mnt/pfs/gbt")
  testData = spark.read.parquet("/mnt/pfs/test.parquet")
  evaluator = MulticlassClassificationEvaluator(labelCol="Survived", predictionCol="prediction", metricName="accuracy")
  gbt_prediction = gbt_model.transform(testData)
  gbt_accuracy = evaluator.evaluate(gbt_prediction)
  print("Accuracy of Gradient-boosted tree classifie is = %g"% (gbt_accuracy))
  print("Test Error of Gradient-boosted tree classifie %g"% (1.0 - gbt_accuracy))

  spark.stop()

if __name__ == "__main__":
  app_ops = os.getenv("APP_OPS")
  if app_ops == 'processing':
    processing()
  elif app_ops == 'training':
    training()
  else:
    scoring()
  import time
  time.sleep(3600)
  