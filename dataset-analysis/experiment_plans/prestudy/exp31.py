#!/usr/bin/env python

"""Workload patterns
Runs an experiment for all 9 sb apps with 4 workload patterns each running for 20 minutes.
The workload patterns create an average load of around 20 requests per second.
"""

# Usage:
# 1) Open tmux
# 2) Activate virtualenv
# 3) Run ./exp31.py 2>&1 | tee exp31.log

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

patterns_dir = Path('/home/ec2-user/20min_20rps')
patterns = [
    'steady.csv',
    'fluctuating.csv',
    'jump.csv',
    'spikes.csv'
]
pattern_paths = [(patterns_dir / a).resolve() for a in patterns]

def run_test(sb, trace):
    try:
        sb.prepare()
        sb.config.set('label', 'exp31.py')
        sb.wait(30)
        sb.invoke('custom', workload_trace=str(trace))
        sb.wait(5*60)
        sb.get_traces()
    except:
        logging.error('Error during execution of benchmark. Cleaning up ...')
    finally:
        sb.cleanup()

# Run all apps with all trace patterns
for sb in sb_clis:
    for trace in pattern_paths:
        run_test(sb, trace)
