#!/usr/bin/env python

"""Request rate
Runs an experiment for all 9 (+1) sb apps with two bursts.
"""

# Usage:
# 1) Open tmux
# 2) Activate virtualenv
# 3) Run ./exp1_latency_breakdown_v3.py 2>&1 | tee exp1_latency_breakdown_v3.log

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

def run_test(sb):
    try:
        sb.prepare()
        sb.config.set('label', 'exp1_latency_breakdown_v3_three_bursts')
        sb.wait(30)
        sb.invoke('custom', workload_options=options)
        sb.wait(5*60)
        sb.get_traces()
        # sb.analyze_traces()
    except:
        logging.error('Error during execution of benchmark. Cleaning up ...')
    # finally:
    #     sb.cleanup()

# run all
for i in range(1):
    for sb in sb_clis:
        run_test(sb)
