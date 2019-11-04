# Pachyderm pipeline demo with Spark 

This pipeline contains four jobs, including `ingestion`, `processing`, `training` and `scoring`. It uses Kaggle's Titanic contest dataset to build a GBT (Gradient-Boosted Trees) classification model and then predict the `Survived` label.

The dataset is first evenly divided into two sets since I want to demonstrate the Pachyderm's data driven feature. By feeding the first half of the dataset to run the pipeline and get the scoring result of the GBT model. Then the second half of the dataset is pumped into pipeline. Pachyderm then automatically run the pipeline to generate another reading of the model scoring.

* Create the repo and pipelines

```command line
# ssh to the cluster first and run pachctl there
# switch to default project
oc project default

cd pachyderm

# create repo and pipeline
pachctl create repo titanic
cd titanic
pachctl put file titanic@master:part-1.csv -f train1.csv
cd ../pipelines
pachctl create pipeline -f ingestion.json
pachctl create pipeline -f processing.json
pachctl create pipeline -f training.json
pachctl create pipeline -f scoring.json
cd ..
```

* Wait for the pipeline to run

Run `oc get pods` and `pachctl list job` to show the progress of the pipeline. At the same time, from the Pachyderm dashboard, the pipeline is moving..

* Explore the `repo`, `pipeline` and `job` from Pachyderm dashboard

The accuracy file `evaluation` is in the `scoring` repo

* Modify training application to use `max_iter=20

```command line
oc edit sparkapplication spark-training
```

change `app_max_iter` to 20. Notice that the pod has been restarted but the pipeline is not rerun.

* Feed more data to pipeline

```command line
cd titanic
pachctl put file titanic@master:part-2.csv -f train2.csv
```

* Wait for the pipeline to rerun

Make sure `oc set env deployment/spark-application-training --list` returns `APP_MAX_ITER: 20`.

* Explore again through Pachyderm dashboard

Notice that there is a new `evaluation` value.

* Other tasks

  - to delete a file from repo

    ```command line
    pachctl delete file titanic@master:part-2.csv
    ```

  - to clean up

    ```command line
    pachctl delete pipeline scoring
    pachctl delete pipeline training
    pachctl delete pipeline processing
    pachctl delete pipeline ingestion
    pachctl delete repo titanic
    oc delete sparkapplication spark-training
    ```
