#!/usr/bin/env python

"""Constant load
Runs an experiment for all 10 sb apps with a given constant load (i.e., load_level) for 90 seconds.
"""

# Usage:
# 1) Open tmux
# 2) Activate virtualenv
# 3) Run ./exp2_load_levels.py 2>&1 | tee -a exp2_load_levels.log

import logging
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

# Load level (rps)
load_level = 1
targets = [load_level]
seconds_per_target = 90
exp_label = f"exp2_load_levels_{load_level}"

# generate custom options
stages = []
for target in targets:
    stages.append({
        'target': target,
        'duration': '1s'
    })
    stages.append({
        'target': target,
        'duration': str(seconds_per_target - 1) + 's'
    })

options = {
    "scenarios": {
        "benchmark_scenario": {
            "executor": "ramping-arrival-rate",
            "startRate": targets[0],
            "timeUnit": "1s",
            "preAllocatedVUs": targets[-1],  # targets[-1],
            "stages": stages
        }
    }
}

def run_test(sb):
    try:
        sb.prepare()
        sb.config.set('label', exp_label)
        sb.config.set('load_level', load_level)
        sb.wait(30)
        sb.invoke('custom', workload_options=options)
        sb.wait(5*60)
        sb.get_traces()
    except:
        logging.error('Error during execution of benchmark. Cleaning up ...')
    finally:
        sb.cleanup()

# run all
for sb in sb_clis:
    run_test(sb)
