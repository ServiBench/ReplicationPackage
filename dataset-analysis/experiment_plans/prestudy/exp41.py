#!/usr/bin/env python

"""Virtual users
Runs an experiment for all 9 sb apps with [1, 10, 20, 50] virtual users for 5 minutes each.
"""

# Usage:
# 1) Open tmux
# 2) Activate virtualenv
# 3) Run ./exp41.py 2>&1 | tee exp41.log

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
    'serverless-faas-workbench/aws/cpu-memory/video_processing/vprocessing_benchmark.py',
    'serverless-faas-workbench/aws/cpu-memory/model_training/mtraining_benchmark.py'
]
app_paths = [(apps_dir / a).resolve() for a in apps]
sb_clis = [Sb(p, log_level='DEBUG', debug=True) for p in app_paths]

# Stepwise pattern with VUs
targets = [1, 10, 20, 50]
seconds_per_target = 5*60


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
            "executor": "ramping-vus",
            "startVUs": targets[0],
            "gracefulRampDown": "0s",
            "stages": stages
        }
    }
}

def run_test(sb):
    try:
        sb.prepare()
        sb.config.set('label', 'exp41.py')
        sb.wait(30)
        sb.invoke('custom', workload_options=options)
        # sb.invoke('spikes')
        sb.wait(5*60)
        sb.get_traces()
        # sb.analyze_traces()
    except:
        logging.error('Error during execution of benchmark. Cleaning up ...')
    finally:
        sb.cleanup()

# run all
for i in range(1):
    for sb in sb_clis:
        run_test(sb)
