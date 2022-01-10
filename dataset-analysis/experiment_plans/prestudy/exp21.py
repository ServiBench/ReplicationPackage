#!/usr/bin/env python

"""Fully constant workload
Runs an experiment for all 9 sb apps with a constant load of 20 request per seconds for 20 minutes.
"""

# Usage:
# 1) Open tmux
# 2) Activate virtualenv
# 3) Run ./exp21.py 2>&1 | tee exp21.log

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

# Stepwise pattern
# targets = [1, 10, 50, 100, 200]
# seconds_per_target = 300

# Constant load
targets = [20]
seconds_per_target = 1200

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
        sb.config.set('label', 'exp21.py')
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

# run single
# run_test(sb_clis[2])

# run all
for i in range(3):
    for sb in sb_clis:
        run_test(sb)
