from minio import Minio
from minio.error import (ResponseError)
import os

app = os.getenv("APP_OPS")
spark_master = os.getenv("SPARK_MASTER")

minioClient = Minio('oc-minio-default.apps.ddoc.os.fyre.ibm.com',
                    access_key='minio',
                    secret_key='minio123',
                    secure=False)
try:
    minioClient.remove_object('titanic', app)
except ResponseError as err:
    print(err)

import uuid
uid = str(uuid.uuid4())

from subprocess import check_output

if app != 'training':
  check_output(['sh', '-c', 'sed -i "s/SPARK_MASTER/%s/g" /opt/app/%s_cr.yaml' % (spark_master, app)]).decode().rstrip()
  check_output(['sh', '-c', '/opt/app/kubectl apply -f /opt/app/%s_cr.yaml' % app]).decode().rstrip()
else:
  try:
    check_output(['sh', '-c', '/opt/app/kubectl get sparkapplication spark-training -o yaml >/tmp/training.yaml']).decode().rstrip()
  except:
    check_output(['sh', '-c', 'sed -i "s/SPARK_MASTER/%s/g" /opt/app/%s_cr.yaml' % (spark_master, app)]).decode().rstrip()
    check_output(['sh', '-c', '/opt/app/kubectl apply -f /opt/app/%s_cr.yaml' % app]).decode().rstrip()
    pass
  else:
    import yaml
    y = yaml.safe_load(open("/tmp/training.yaml"))
    del y["status"]
    del y["metadata"]["annotations"]
    del y["metadata"]["creationTimestamp"]
    del y["metadata"]["generation"]
    del y["metadata"]["resourceVersion"]
    del y["metadata"]["selfLink"]
    del y["metadata"]["uid"]
    y["spec"]["app_name"] = "demo-" + uid
    yaml.dump(y, open("/tmp/training.yaml",'w'), default_flow_style=False)
    check_output(['sh', '-c', '/opt/app/kubectl apply -f /tmp/training.yaml']).decode().rstrip()

# wait until pipeline job complete
for x in range(120):
  try:
      minioClient.stat_object('titanic', app)
  except:
      import time
      time.sleep(5)
      pass
  else:
      f = open('/pfs/out/%s' % app, 'w')
      f.write("Done " + uid)
      f.close()

if app == 'scoring':
  try:
      print(minioClient.fget_object('titanic', 'scoring', '/pfs/out/evaluation'))
  except ResponseError as err:
      print(err)

if app != 'training':
  check_output(['sh', '-c', '/opt/app/kubectl delete -f /opt/app/%s_cr.yaml' % app]).decode().rstrip()