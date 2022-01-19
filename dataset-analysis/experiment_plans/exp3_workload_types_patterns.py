#!/usr/bin/env python

"""Invocation patterns workload types
Runs an experiment with 4 typical serverless invocation patterns:
a) steady: (32.5\%) represents stable load with low burstiness
b) fluctuating: (37.5\%) combines a steady base load with continuous load fluctuations especially characterized by short bursts
c) spikes: (22.5\%) represents occasional extreme load bursts with or without a steady base load
d) jump: (7.5\%) represents sudden load changes maintained for several minutes before potentially returning to a steady base load.
"""

# Usage:
# 1) Open tmux
# 2) Activate virtualenv: source sb-env/bin/activate
# 3) Run ./exp3_workload_types_patterns.py 2>&1 | tee -a exp3_workload_types_patterns.log

import logging
from pathlib import Path
from sb.sb import Sb

apps_dir = Path('/home/ec2-user')
# App-specific target invocation rates (r/sec) based on the scalability experiment.
# 50% of last load level.
apps_load_level_mapping = {
    'faas-migration/ThumbnailGenerator/Lambda/thumbnail_benchmark.py': 37,
    'faas-migration/MatrixMultiplication/Lambda/matrix_multiplication_benchmark.py': 10,
    'faas-migration/Event-Processing/Lambda/event_processing_benchmark.py': 50,
    'aws-serverless-workshops/ImageProcessing/image_processing_benchmark.py': 25,
    'faas-migration-go/aws/todo_api_benchmark.py': 200,
    'hello-retail/hello_retail_benchmark.py': 154,
    'realworld-dynamodb-lambda/realworld_benchmark.py': 167,
    'serverless-faas-workbench/aws/cpu-memory/video_processing/video_processing_benchmark.py': 25,
    'serverless-faas-workbench/aws/cpu-memory/model_training/model_training_benchmark.py': 22,
    'serverless-patterns/apigw-lambda-cdk/src/apigw_node_benchmark.py': 200
}

sb_clis = []
for app, load_level in apps_load_level_mapping.items():
    app_path = (apps_dir / app).resolve()
    sb_cli = Sb(app_path, log_level='DEBUG', debug=True)
    sb_clis.append((sb_cli, load_level))

# Built-in 20min patterns
patterns = [
    'steady',
    'fluctuating',
    'jump',
    'spikes'
]

# Alternatively load from custom csv file.
# patterns_dir = Path('/home/ec2-user/20min_pick')
# patterns = [
#     'steady.csv',
#     'fluctuating.csv',
#     'jump.csv',
#     'spikes.csv'
# ]
# pattern_paths = [(patterns_dir / a).resolve() for a in patterns]

def run_test(sb, load_level, pattern):
    workload_label = pattern
    ## Derive label
    exp_label = f"exp3_workload_types_20min_{workload_label}"
    try:
        sb.prepare()
        sb.config.set('label', exp_label)
        sb.config.set('load_level', load_level)
        sb.config.set('workload_label', workload_label)
        sb.wait(30)
        sb.invoke(pattern, scale_rate_per_second=load_level)
        sb.wait(5*60)
        sb.get_traces()
    except:
        logging.error('Error during execution of benchmark. Cleaning up ...')
    finally:
        sb.cleanup()

# run all
for sb, load_level in sb_clis:
    for pattern in patterns:
        run_test(sb, load_level, pattern)
