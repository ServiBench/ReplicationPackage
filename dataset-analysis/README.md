# SB Traces Dataset

This repository contains scripts and instructions to reproduce:

* a) the data analysis based on our published dataset
* b) the cloud experiments in a serverless cloud environment using sb.
* c) the invocation pattern analysis based on the Azure Function Traces dataset (see [azurefunctions-dataset2019-analysis](https://github.com/perfkit/azurefunctions-dataset2019-analysis))

## Data Analysis

We first use the sb trace analyzer to pre-process the raw traces before generating plots.

### Preparation

1. Activate virtual environment with sb

    ```sh
    source sb-env/bin/activate  # depends on shell
    ```

2. Pre-process traces through sb analyzer

    ```sh
    make analyze_traces
    ```

### Generate Plots

1. Install Python 3.7+
2. Create virtual environment

    ```sh
    python3 -m venv sb-dataset-analysis
    ```

3. Install the Python dependencies

    ```sh
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

4. Generate plots

    a) Plain Python

      ```sh
      make generate_plots
      make generate_plots_all
      ```

    b) VSCode Interactive: Run individual cells with the [Python extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python) in [interactive mode](https://youtu.be/lwN4-W1WR84?t=107)

> The data source can be configured via `SB_DATA_SOURCE` (default `lg12`) or directly through `SB_DATA_DIR` (default `data/lg12/raw`).

## Cloud Experiments

We describe how to reproduce our experiments in the AWS cloud environment to collect a new dataset following the same experiment design.

> Carefully review the experiment configuration and be aware that experiments with high-load levels can cost 1000s of USD in cloud bills!

### Preparation

1. Create an AWS account for sb following [these instructions](https://github.com/perfkit/serverless-benchmarker/blob/master/docs/AWS.md)
2. Create an [X-Ray sampling rule](https://docs.aws.amazon.com/xray/latest/devguide/xray-console-sampling.html) called `NoSampling` with highest priority (`1`) and 100% fixed sampling rate.

### Run Experiments

1. Set up a load generator in AWS EC2 following [these instructions](https://github.com/perfkit/serverless-benchmarker/blob/master/docs/LOADGENERATOR.md). Use the alias `lg12` in the SSH config or adjust set the environment variable `SB_DATA_SOURCE` for the following steps.
2. Copy the [experiment_plans](./experiment_plans) into the load generator

    ```sh
    scp experiment_plans/exp* ec2-user@lg12:/home/ec2-user
    ```

3. Run the experiment as described in each experiment plan using `tmux` because ordinary SSH sessions might disconnect during long running experiments. The experiment plans automate the benchmarking lifecycle including application deployment, trace collection, and application cleanup.
4. Download the collected traces using `make retrieve_logs`
