# ServiBench Replication Package
The replication package for our manuscript _Let's Trace It: Fine-Grained Serverless Benchmarking using Synchronous and Asynchronous Orchestrated Applications_ consists of the ServiBench tool, our analysis of the azure workload traces, the ten benchmarking applications+benchmarking harness, and our analysis of the obtained dataset:
* [ServiBench (sb)](#ServiBench-(sb))
* [Analysis of the Azure Workload Traces](#Analysis-of-the-Azure-Workload-Traces)
* [Benchmarking Applications](#Benchmarking-Applications)
    * [Minimal Baseline](#Minimal-Baseline)
    * [Thumbnail Generator](#Thumbnail-Generator)
    * [Event Processing](#Event-Processing)
    * [Facial Recognition](#Facial-Recognition)
    * [Model Training](#Model-Training)
    * [Realworld Backend](#Realworld-Backend)
    * [Hello Retail!](#Hello-Retail)
    * [Todo API](#Todo-API)
    * [Matrix Multiplication](#Matrix-Multiplication)
    * [Video Processing](#Video-Processing)
* [Analysis of the obtained Dataset](#Analysis-of-the-obtained-Dataset)

## ServiBench (sb)
ServiBench (sb) is a meta-benchmarking tool to orchestrate reproducible serverless application benchmarking.

* **Reproducible deployments**: sb abstracts away dependencies using Docker and automatically mounts application code and credentials (when needed) into the right container directories.
* **Automated load generation**: sb provides different classes of invocation patterns derived from real-world traces. It integrates with the open source load testing tool [k6](https://k6.io/).
* **Clear box application insights**: for instrumented applications, sb implements detailed trace analysis using distributed tracing such as [AWS X-Ray](https://aws.amazon.com/xray/) and [Azure Application Insights](https://docs.microsoft.com/en-us/azure/azure-monitor/app/distributed-tracing).

### Quick Setup

1. Install [Docker](https://docs.docker.com/get-docker/) 19.03+
2. Install [Python](https://www.python.org/downloads/) 3.7+ (tested with 3.7, 3.8. 3.9, 3.10)

    > ARM-based Apple M1 systems are not yet fully supported. The trace analyzer works with Python 3.10 but the Docker integration can cause some problems with certain applications.

3. Install the `sb` tool:

    a) [pipx](https://packaging.python.org/guides/installing-stand-alone-command-line-tools/) (recommended for CLI)

    ```bash
    python3 -m pip install --upgrade pip
    python3 -m pip install --user pipx
    python3 -m pipx ensurepath  # might require terminal restart
    cd serverless-benchmarker
    pipx install --editable .
    ```

    b) [venv](https://docs.python.org/3/library/venv.html) (required for SDK when using the programmatic API)

    ```bash
    python3 -m venv sb-env
    source sb-env/bin/activate  # depends on shell
    cd serverless-benchmarker
    python3 -m pip install --upgrade pip
    pip install --editable .
    ```

4. Build the sb Dockerfile via `sb init`
5. Login for providers via `sb login PROVIDER`: Supported for [aws](./serverless-benchmarker/docs/AWS.md), [azure](./serverless-benchmarker/docs/AZURE.md), `google`, `ibm`.

### Credentials

The credentials are stored in a Docker volume called `PROVIDER-secrets` (e.g., `aws-secrets`) and selectively mounted when needed. They can be deleted via `sb logout PROVIDER`.
Check credentials via `sb check_credentials PROVIDER`

### Getting Started

```sh
# Run empty mock benchmark locally
sb test --file=tests/fixtures/mock_benchmark/mock_benchmark.py

# Get an AWS and Azure app
git clone git@github.com:anonymous/faas-migration.git
# AWS
cd faas-migration/ThumbnailGenerator/Lambda
# Azure
cd faas-migration/ThumbnailGenerator/Azure

# Benchmarking lifecycle using a `*_benchmark.py` file:
# 1) Deploy app
sb prepare
# 2a) Invoke app a single time
sb invoke
# 2b) Invoke app 10 times sequentially
sb invoke 10
# 2c) Benchmark with a pre-configured workload_type (steady|fluctuating|spikes|jump)
sb invoke fluctuating
# 3) Download traces
sb get_traces
# 4) Analyze latest traces
sb analyze_traces
# Hint for analyzing previous traces: sb analyze_traces logs/DATETIME/traces.json
# 5) Cleanup all cloud infrastructure
sb cleanup
```

*Hints:*

* `*_benchmark.py` files in the current working directory are automatically detected (if only a single file exists).
* `sb test` sequentially executes prepare, invoke (with workload_type=3) and, cleanup.
* `sb invoke custom_per_minute_rate_trace.csv` supports custom CSV workload traces.
* Checkout the [AWS X-Ray Console](https://console.aws.amazon.com/xray/home) for result traces (6h retention!) or [CloudWatch logs](https://console.aws.amazon.com/cloudwatch).


### Debugging

* `sb shell IMAGE` starts an interactive shell with all auto-mounts in a given Docker IMAGE.
* More examples of `*_benchmark.py` files are available under `tests/fixtures` (covered by integration tests)
* Insert the code `import code; code.interact(local=dict(globals(), **locals()))` on any line to prompt an interactive Python shell.
* Checkout the [DEVELOPMENT](./serverless-benchmarker/docs/DEVELOPMENT.md) docs for more details.


### Adding a custom application

1. Create a `*_benchmark.py` file in the main directory of your application.
2. Implement hooks for `prepare(spec)`, `invoke(spec)`, and `cleanup(spec)` as shown under [mock_benchmark.py](.serverless-benchmarker/tests/fixtures/mock_benchmark/mock_benchmark.py). Key functionality:
    * `spec.run(CMD, image=DOCKERIMAGE)` Runs a given CMD in a DOCKERIMAGE and returns its stdout.
    * `spec.build(IMAGE_TAG)` Builds a Dockerfile and tags it with IMAGE_TAG.
    * `spec['KEY']` provides a persistent key-value store across different benchmark cycles (e.g., share state between prepare and invoke)
    * The `BENCHMARK_CONFIG` constant initializes the key-value store and specifies configurable attributes (e.g., region) and meta-information (e.g., provider).
    * The working directory is defined by the location of `*_benchmark.py` (i.e., same directory).
    * sb mounts the working directory by default into any Docker container. If files at higher levels are required, the `root` benchmark config allows to mount higher level directories (e.g., parent using `..`).
    * sb integrates with [k6](https://k6.io/) for load testing.
    * `sb invoke` automatically generates a `workload_options.json` file with [k6 options](https://k6.io/docs/using-k6/options).
    * `sb invoke` and `sb get_traces` automatically create logs in the working directory under `logs` with the start timestamp of the invocation.
3. Instrument your application (provider- and language-dependent):
    * AWS: Enable X-Ray tracing and add language-specific instrumentation as described [here](https://docs.aws.amazon.com/lambda/latest/dg/services-xray.html).
    * Azure: TODO(clarify how to use [Azure Insights](https://docs.microsoft.com/en-us/azure/azure-monitor/app/app-insights-overview) metrics for [distributed tracing](https://docs.microsoft.com/en-us/azure/azure-monitor/app/distributed-tracing))

### Further documentation
* [AWS](./serverless-benchmarker/docs/AWS.md)
* [Azure](./serverless-benchmarker/docs/AZURE.md)
* [Design](./serverless-benchmarker/docs/DESIGN_V1.md)
* [Development](./serverless-benchmarker/docs/DEVELOPMENT.md)
* [FAQ](./serverless-benchmarker/docs/FAQ.md)
* [Load Generator](./serverless-benchmarker/docs/LOADGENERATOR.md)
* [Output](./serverless-benchmarker/docs/OUTPUT.md)

## Analysis of the Azure Workload Traces
We visually identify 4 typical invocation patterns from the azure functions dataset by manually classifying two time ranges for 100 of the 528 functions remaining after the initial filtering. We first created 200 individual line plots with invocation counts over 20 minutes and grouped similar traffic shapes into several clusters. After merging similar patterns, we identified the following 4 common patterns:
* Steady (32.5%) represents stable load with low burstiness
* Fluctuating (37.5%) combines a steady base load with continuous load fluctuations especially characterized by short bursts
* Spikes (22.5%) represents occasional extreme load bursts with or without a steady base load
* Jump (7.5%) represents sudden load changes maintained for several minutes before potentially returning to a steady base load.

To replicate our visual analysis and to obtain the data behind the four patterns we selected, follow the following steps. This analysis was conducted in R and therefore requires an up-to-date installation of R.

```
Follow the instructions in azuredataset-analysis/code/01_download.R to download the azure dataset
```

Next, to preprocess the data run the following command (make sure that the dataset is available and the path to it is set correctly): 

```
Rscript azuredataset-analysis/code/02_merge_2weeks.R
```

To visualize the individual traces, run the following command after preprocessing the data:

```
Rscript azuredataset-analysis/03_plot_invocations.R
```

Finally, to export the four example traces we selected, run the following command (after the preprocessing): 

```
Rscript azuredataset-analysis/04_export_traces.R
```

The resulting traces can be used with our framework to run performance experiments with any of the available applications.

## Benchmarking Applications
ServiBench supports the following ten applications out of the box. See [Adding a custom application](#Adding-a-custom-application) for information on how to integrate additional applications.
### Minimal Baseline
This application implemetnts the API Gateway + Lambda pattern and serves as our minimal baseline for a serverless application.
<p align="left">
<img src="./figures/baseline.png?raw=true" width="200">
</p>
This application is from Serverlessland (https://serverlessland.com/patterns/apigw-lambda-cdk) and was forked from the https://github.com/aws-samples/serverless-patterns/ repository. To use this application, run the following commands:


```
cd serverless-patterns/src/
sb prepare
sb invoke fluctuating
sb get_traces
sb analyze_traces
sb cleanup
```


### Thumbnail Generator
The Thumbnail Generator application generates a thumbnail of an image uploaded to a storage bucket. The first function implements an HTTP API to upload an image to a storage
bucket. The storage event then triggers a second function to generate a thumbnail of the image and store it in another storage bucket.
<p align="left">
<img src="./figures/Thumbnail.png?raw=true" width="500">
</p>

This application is from the following study by Yussupov et al.:

```
Vladimir Yussupov, Uwe Breitenbücher, Frank Leymann, and Christian Müller. Facing the unplanned migration of serverless applications: A study on portability problems, solutions, and dead ends. In Proceedings of the 12th IEEE/ACM International Conference on Utility and Cloud Computing, pages 273–283, 2019.
```

It was originally forked from the https://github.com/iaas-splab/faas-migration repository. To use this application, run the following commands:

```
cd applications/faas-migration/ThumbnailGenerator/Lambda
sb prepare
sb invoke fluctuating
sb get_traces
sb analyze_traces
sb cleanup
```

### Event Processing
The Event Processing application generates and inserts event into an input queue. The queue triggers a lambda which pre-processes the event and places it in the ingested queue.
The placement of an event in the ingested queue triggers another lambda to process the event and store the results in the database.
<p align="left">
<img src="./figures/Event.png?raw=true" width="500">
</p>

This application is from the following study by Yussupov et al.:

```
Vladimir Yussupov, Uwe Breitenbücher, Frank Leymann, and Christian Müller. Facing the unplanned migration of serverless applications: A study on portability problems, solutions, and dead ends. In Proceedings of the 12th IEEE/ACM International Conference on Utility and Cloud Computing, pages 273–283, 2019.
```

It was originally forked from the https://github.com/iaas-splab/faas-migration repository. To use this application, run the following commands:

```
cd applications/faas-migration/Event-Processing/Lambda
sb prepare
sb invoke fluctuating
sb get_traces
sb analyze_traces
sb cleanup
```

### Facial Recognition
Facial Recognition app takes a user uploaded image, extracts a face from it, and detects if the face already exists in the database. If the face does not already exist in the database, the app indexes the face and saves a thumbnail of the face to object storage.
<p align="left">
<img src="./figures/face.png?raw=true" width="500">
</p>

This application is part of the AWS Wild Rydes workshop (https://www.image-processing.serverlessworkshops.io/) and was cloned from the https://github.com/aws-samples/aws-serverless-workshops/ repository.To use this application, run the following commands:

```
cd applications/aws-serverless-workshops/ImageProcessing/
sb prepare
sb invoke fluctuating
sb get_traces
sb analyze_traces
sb cleanup
```

### Model Training
Model Training application reads datasets from object storage, trains machine learning models on those datasets, and stores the trained models in object storage.
<p align="left">
<img src="./figures/ModelTraining.png?raw=true" width="500">
</p>

This application is from the following publication by Kim et al.:

```
Jeongchul Kim and Kyungyong Lee. FunctionBench: A suite of workloads for serverless cloud function service. In Proceedings of the 12th IEEE International Conference on Cloud Computing (CLOUD WIP), pages 502–504, 2019.
```

It was originally forked from the https://github.com/kmu-bigdata/serverless-faas-workbench repository. To use this application, run the following commands:

```
cd applications/serverless-faas-workbench/aws/cpu-memory/model_training/
sb prepare
sb invoke fluctuating
sb get_traces
sb analyze_traces
sb cleanup
```

### Realworld Backend
RealWorld Backend uses a FaaS to create, read, update, and delete user and article information stored in a database.
<p align="left">
<img src="./figures/Realworld.png?raw=true" width="500">
</p>

This application is an AWS implementation of the real world spec (https://github.com/gothinkster/realworld) and was forked from the https://github.com/anishkny/realworld-dynamodb-lambda repository. To use this application, run the following commands:

```
cd applications/faas-migration-go/aws
sb prepare
sb invoke fluctuating
sb get_traces
sb analyze_traces
sb cleanup
```

### Hello Retail
The Hello Retail! is a retail inventory catalog application backed by a database. Users can upload product information and categorize products into categories. Supports sending an SMS if a product does not have an image. Uploaded images are stored in object storage.
<p align="left">
<img src="./figures/Retail.png?raw=true" width="500">
</p>

This application was forked from the https://github.com/etsangsplk/hello-retail repository. To use this application, run the following commands:

```
cd applications/hello-retail
sb prepare
sb invoke fluctuating
sb get_traces
sb analyze_traces
sb cleanup
```
### Todo API
The Todo API application is a simple to-do app which uses a FaaS to create, read, update, and delete todos stored in a database. 
<p align="left">
<img src="./figures/Todo.png?raw=true" width="500">
</p>

This application is from the following study by Yussupov et al.:

```
Vladimir Yussupov, Uwe Breitenbücher, Frank Leymann, and Christian Müller. Facing the unplanned migration of serverless applications: A study on portability problems, solutions, and dead ends. In Proceedings of the 12th IEEE/ACM International Conference on Utility and Cloud Computing, pages 273–283, 2019.
```

It was originally forked from the https://github.com/iaas-splab/faas-migration repository. To use this application, run the following commands:

```
cd applications/faas-migration-go/aws
sb prepare
sb invoke fluctuating
sb get_traces
sb analyze_traces
sb cleanup
```
### Matrix Multiplication
The Matrix Multiplication application generates a random matrix, partitions the matrix, and distributes it for multiplication. Workers perform the multiplication and write the results to S3. The results are then combined to get the final result of the multiplication. The app is directed by an orchestration service.
<p align="left">
<img src="./figures/matrix.png?raw=true" width="500">
</p>

This application is from the following study by Yussupov et al.:

```
Vladimir Yussupov, Uwe Breitenbücher, Frank Leymann, and Christian Müller. Facing the unplanned migration of serverless applications: A study on portability problems, solutions, and dead ends. In Proceedings of the 12th IEEE/ACM International Conference on Utility and Cloud Computing, pages 273–283, 2019.
```

It was originally forked from the https://github.com/iaas-splab/faas-migration repository. To use this application, run the following commands:

```
cd applications/faas-migration/MatrixMultiplication/Lambda
sb prepare
sb invoke fluctuating
sb get_traces
sb analyze_traces
sb cleanup
```
### Video Processing
The Video Processing application reads videos from object storage, applies filters, and transcodes them. The transcoded videos are stored in object storage.
<p align="left">
<img src="./figures/Video.png?raw=true" width="500">
</p>

This application is from the following publication by Kim et al.:

```
Jeongchul Kim and Kyungyong Lee. FunctionBench: A suite of workloads for serverless cloud function service. In Proceedings of the 12th IEEE International Conference on Cloud Computing (CLOUD WIP), pages 502–504, 2019.
```

It was originally forked from the https://github.com/kmu-bigdata/serverless-faas-workbench repository. To use this application, run the following commands:

```
cd applications/serverless-faas-workbench/aws/cpu-memory/video_processing/
sb prepare
sb invoke fluctuating
sb get_traces
sb analyze_traces
sb cleanup
```

## Analysis of the obtained Dataset
1. Install Python 3.7+
2. Install the Python dependencies (preferably in a virtual environment)

    ```sh
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

3. Adjust the data source path in `sb_importer.py` (data_path and lg_name)
4. Run analysis

    a) Plain Python

      ```sh
      python coldstart_behavior.py
      python workload_types.py
      python load_levels.py
      python execution.py
      ```

    b) VSCode Interactive: Run individual cells with the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) in [interactive mode](https://youtu.be/lwN4-W1WR84?t=107)
