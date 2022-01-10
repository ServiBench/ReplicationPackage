#!/usr/bin/env python

"""Stepwise increasing load
Runs an experiment for the thumbnail_generator app with a stepwise increasing load pattern of
[1, 10, 20, 50, 100, 150, 200, 500, 750, 1000] requests per second for 5 minutes each.
"""

# Usage:
# 1) Open tmux
# 2) Activate virtualenv
# 3) Run ./exp44.py 2>&1 | tee exp44.log

import logging
from pathlib import Path
from sb.sb import Sb

apps_dir = Path('/home/ec2-user')
apps = [
    'faas-migration/ThumbnailGenerator/Lambda/thumbnail_benchmark.py'
    # 'faas-migration/Event-Processing/Lambda/event_processing_benchmark.py'
]
app_paths = [(apps_dir / a).resolve() for a in apps]
sb_clis = [Sb(p, log_level='DEBUG', debug=True) for p in app_paths]

# Stepwise pattern
targets = [1, 10, 20, 50, 100, 150, 200, 500, 750, 1000]
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
        sb.config.set('label', 'exp44.py')
        sb.invoke('custom', workload_options=options)
        sb.wait(5*60)
        sb.get_traces()
    except:
        logging.error('Error during execution of benchmark. Cleaning up ...')
    finally:
        sb.cleanup()

# run all
for i in range(1):
    for sb in sb_clis:
        run_test(sb)
