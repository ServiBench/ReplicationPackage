#!/usr/bin/env python

"""Stepwise increasing load
Runs an experiment for the thumbnail_generator app with a stepwise increasing load pattern of
(see list per app) requests per second for 10 seconds each.
"""

# Usage:
# 1) Open tmux
# 2) Activate virtualenv
# 3) Run ./exp81_xray_sampling.py 2>&1 | tee exp81_xray_sampling.py.log

import logging
from pathlib import Path
from sb.sb import Sb

apps_dir = Path('/home/ec2-user')
apps = [
    # [1, 10, 20, 50, 100, 150, 200, 250]
    # 'faas-migration/ThumbnailGenerator/Lambda/thumbnail_benchmark.py'
    # [10, 20, 50, 100, 150, 200, 250, 300, 400, 500]
    'faas-migration-go/aws/todo_api_benchmark.py'
]
app_paths = [(apps_dir / a).resolve() for a in apps]
sb_clis = [Sb(p, log_level='DEBUG', debug=True) for p in app_paths]

# Stepwise pattern
targets = [10, 20, 50, 100, 150, 200, 250, 300, 400, 500]
seconds_per_target = 10

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
        sb.wait(30)
        sb.config.set('label', 'exp81_xray_sampling.py')
        sb.invoke('custom', workload_options=options)
        sb.wait(10*60)
        sb.get_traces()
    except:
        logging.error('Error during execution of benchmark. Cleaning up ...')
    finally:
        sb.wait(5*60)
        sb.cleanup()

# run all
for i in range(1):
    for sb in sb_clis:
        run_test(sb)
