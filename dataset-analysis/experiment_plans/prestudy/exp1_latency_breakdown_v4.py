#!/usr/bin/env python

"""Bursts (exp1_latency_breakdown_4x_burst20)
Runs an experiment for all 10 sb apps with 4 bursts of concurrency 20 and redeployment after 10 trials.
This experiment plan aims to produce multiple full cold starts (i.e., max number of cold starts per app) per trial,
followed by a series of warm invocations with the same burst size.
Redeployments resets each application completely to mitigate potential memory effects of previous invocations.
Redeployments are performed only periodically because they take a lot of time (up to 50 min) for certain applications.

Changelog:
* v1 30 VUs and 20 VUs overloads several apps + X-Ray on Lambda (1 VU takes too long for collecting cold invocation samples)
* v2 120 rps overloads longer running apps
* v3 3 bursts of 20 VUs for single run
* v4 4 bursts of 20 VUs and periodic redeployment
"""

# Usage:
# 1) Open tmux
# 2) Activate virtualenv
# 3) Run ./exp1_latency_breakdown_v4.py 2>&1 | tee -a exp1_latency_breakdown_v4.log

import logging
import sys
from pathlib import Path
from sb.sb import Sb

apps_dir = Path('/home/ec2-user')
apps = [
    'faas-migration/ThumbnailGenerator/Lambda/thumbnail_benchmark.py',
    'faas-migration/MatrixMultiplication/Lambda/matrix_multiplication_benchmark.py',
    'faas-migration/Event-Processing/Lambda/event_processing_benchmark.py',
    'aws-serverless-workshops/ImageProcessing/image_processing_benchmark.py',
    'faas-migration-go/aws/todo_api_benchmark.py',
    'hello-retail/hello_retail_benchmark.py',
    'realworld-dynamodb-lambda/realworld_benchmark.py',
    'serverless-faas-workbench/aws/cpu-memory/video_processing/video_processing_benchmark.py',
    'serverless-faas-workbench/aws/cpu-memory/model_training/model_training_benchmark.py',
    'serverless-patterns/apigw-lambda-cdk/src/apigw_node_benchmark.py'
]
app_paths = [(apps_dir / a).resolve() for a in apps]
sb_clis = [Sb(p, log_level='DEBUG', debug=True) for p in app_paths]

# Repetition configuration
num_repetitions = 12
num_trials = 10
exp_label = 'exp1_latency_breakdown_4x_burst20'
# abort experiment if more errors occur (excluding retries)
error_threshold = 10
error_count = 0

# There is currently no way to declare dependencies in k6 such that
# one scenario starts after another apart from startTime. See:
# https://community.k6.io/t/if-the-current-scenario-does-not-have-a-fixed-time-how-can-the-next-scenario-start-after-this-one-is-finished/2112
options = {
    "scenarios": {
        "cold_burst": {
            "executor": "per-vu-iterations",
            "vus": 20,
            "iterations": 1
        },
        "warm_burst1": {
            "executor": "per-vu-iterations",
            "vus": 20,
            "iterations": 1,
            "startTime": "60s"
        },
        "warm_burst2": {
            "executor": "per-vu-iterations",
            "vus": 20,
            "iterations": 1,
            "startTime": "120s"
        },
        "warm_burst3": {
            "executor": "per-vu-iterations",
            "vus": 20,
            "iterations": 1,
            "startTime": "180s"
        },
    }
}


def run_trial(sb):
    """Invokes and downloads traces"""
    sb.wait(10)
    sb.invoke('custom', workload_options=options)
    # 2 minutes waiting time should be sufficient for apps to complete
    # and for the X-Ray traces to be processed when using only 60 invocations from 4 bursts of 20.
    sb.wait(2*60)
    sb.get_traces()


def prepare_with_retry(sb):
    """Prepare a benchmark with a single retry"""
    try:
        sb.prepare()
        sb.config.set('label', exp_label)
    except:
        logging.error('Error during preparation of benchmark. Cleaning up and re-trying.')
        sb.cleanup()
        sb.prepare()
        sb.config.set('label', exp_label)


def cleanup_with_retry(sb):
    """Cleanup a benchmark with a single retry"""
    try:
        sb.cleanup()
    except:
        logging.error('Error during cleanup of benchmark. Re-trying.')
        sb.cleanup()


# Experiment execution plan
for repetition in range(num_repetitions):
    for trial in range(num_trials):
        for sb in sb_clis:
            try:
                # Startup: prepare before first trial
                if trial == 0:
                    prepare_with_retry(sb)
                # Run
                logging.info(f"benchmark={sb.name()};repetition={repetition+1}/{num_repetitions};trial={trial+1}/{num_trials}")
                run_trial(sb)
                # Cleanup: cleanup after last trial
                if trial == num_trials-1:
                    cleanup_with_retry(sb)
            except:
                logging.error(f"Error during execution of benchmark {sb.name()}. Skip current trial.")
                error_count += 1
                if error_count > error_threshold:
                    logging.error(f"Exceeded error threshold with {error_count} errors. Cleaning up and aborting.")
                    for sb in sb_clis:
                        cleanup_with_retry(sb)
                    sys.exit("Aborted after exceeding error threshold.")
