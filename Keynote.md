0. First clone the dday2019 repo

```command line
git clone git@github.ibm.com:wzhuang/dday2019.git
```

1. Prepare artifacts for the application, including docker images etc.

```command line
wget http://ftp.wayne.edu/apache/spark/spark-2.4.4/spark-2.4.4-bin-hadoop2.7.tgz
tar zxvf spark-2.4.4-bin-hadoop2.7.tgz
cd spark-2.4.4-bin-hadoop2.7
cp ../patch/run.sh sbin
cp ../patch/Dockerfile kubernetes/dockerfiles/spark
./bin/docker-image-tool.sh -r docker.io/adrian555 -t v2.4.4 build
./bin/docker-image-tool.sh -r docker.io/adrian555 -t v2.4.4 push
cd ..
```

* modify [Dockerfile](patch/Dockerfile)
* can also push to quay.io

2. Run operator-sdk command to create an Ansible type operator.

```command line
operator-sdk new spark-operator --api-version=ibm.com/v1alpha1 --kind=Spark --type=ansible
```

* look inside the [directory](spark-operator)

3. Modify the scaffolding code to build the operator:

```command line
rm -rf spark-operator
mv spark-operator.full spark-operator
```

* Add the tasks to ansible [playbook](spark-operator/roles/spark)
* Modify or add CRDs and [CRs](spark-operator/deploy/crds)
* Modify the role and [rolebinding](spark-operator/deploy/role)
* Build docker image for the operator

```command line
cd spark-operator
operator-sdk build adrian555/spark-operator:v0.0.1
docker push adrian555/spark-operator:v0.0.1
cd ..
```

* Update [Deployment](spark-operator/deploy/operator.yaml) to use the docker image

```command line
cd spark-operator
sed -i '' 's/{{ REPLACE_IMAGE }}/adrian555\/spark-operator:v0.0.1/g' deploy/operator.yaml
sed -i '' 's/imagePullPolicy:.*$/imagePullPolicy: Always/g' deploy.operator.yaml
cd ..
```

Now the operator code is ready for manual install.

4. Two approaches to install the operator and deploy application.

- Install manually

  ```command line
  # login to the cluster
  oc login --token=80Q3X5wIeveTbcQrWlWJwGvpN5ZhOIQ3Igrye5Gx42o --server=https://api.ddoc.os.fyre.ibm.com:6443

  # create a new project
  oc new-project dday2019
  oc adm policy add-scc-to-user anyuid -z default
  ```

    - create CRDs
    - create serviceaccount
    - create role and rolebinding
    - create the operator deployment

    ```command line
    cd spark-operator
    ls deploy/crds
    oc apply -f deploy/crds/ibm_v1alpha1_spark_crd.yaml
    oc apply -f deploy/service_account.yaml
    oc apply -f deploy/role.yaml
    oc apply -f deploy/role_binding.yaml
    oc apply -f deploy/operator.yaml
    ```

    To check the progress

    ```command line
    kubectl logs deployment/spark-operator operator -n dday2019 -f
    ```

    - deploy the application with customresource

    ```command line
    oc apply -f deploy/crds/ibm_v1alpha1_spark_cr.yaml
    ```

    To check the progress
    
    ```command line
    kubectl logs deployment/spark-operator operator -n dday2019 -f
    ```

    Once the application has been installed, look at the pod and service

    ```command line
    oc get pods
    oc get svc
    ```

    - run [Spark pi demo](http://ddoc-inf.fyre.ibm.com:9090/notebooks/demo.ipynb)
    - do some cleanup
    
    ```command line
    cd spark-operator
    oc delete -f deploy/crds/ibm_v1alpha1_spark_cr.yaml
    oc delete -f deploy/operator.n.yaml
    oc delete -f deploy/role_binding.yaml
    oc delete -f deploy/role.yaml
    oc delete -f deploy/service_account.yaml
    oc delete -f deploy/crds/ibm_v1alpha1_spark_crd.yaml
    ```

- Install through OLM
    - generate [clusterserviceversion](spark-operator/deploy/olm-catalog/)
  
    ```command line
    cd spark-operator
    operator-sdk olm-catalog gen-csv --csv-version 0.0.1 --update-crds
    cd ..
    ```

    - update csv and verify with [operator-courier](spark-operator/deploy/olm-catalog)

    ```command line
    # verify the current generated one
    cd spark-operator/deploy/olm-catalog
    operator-courier verify spark-operator

    # replace with the updated one and verify
    cd ..
    rm -rf olm-catalog
    mv olm.new olm-catalog
    cd olm-catalog
    operator-courier verify spark-operator
    cd ../../..
    ```

    - build image for [operator-registry](olm)

    ```command line
    # copy the csv
    cd olm
    mkdir operators
    cp -r ../spark-operator/deploy/olm-catalog/spark-operator operators

    # build the registry image
    docker build . -t adrian555/spark-operator-registry:v0.0.1
    docker push adrian555/spark-operator-registry:v0.0.1
    ```
    - create catalogsource using the registry image
      - if the sourcenamespace has an operatorgroup watching the targetnamespaces, then the operator can be installed to the targetnamespace
      - otherwise, need to create an operatorgroup
    
    ```command line
    # create the catalogsource, source namespace is set to openshift-operator-lifecycle-manager
    oc apply -f catalogsource.yaml

    # check the catalog service is running
    oc get pods -n openshift-operator-lifecycle-manager
    oc get svc -n openshift-operator-lifecycle-manager

    # the operator is now shown
    oc get packagemanifest -n openshift-operator-lifecycle-manager

    cd -
    ```

    We can now look for this operator from the console, click through `Catalog|Operator Management|Operator Catalogs`.

    - create the operator deployment with a subscription
    
    The OperatorGroup in the `openshift-operator-lifecycle-manager` will install the operator to `openshift-operators` namespace

    - deploy the application by creating an instance of the provided API (the CR Spark instance)

    Update the `worker_size` to 2 from `Installed Operator` in `openshift-operators` namespace.