#!/usr/bin/env python

"""Constant vs bursty load pattern
Runs an experiment for all the event_processing app with two different load patterns for 1h.
"""

# Usage:
# 1) Open tmux
# 2) Activate virtualenv
# 3) Run ./exp61.py 2>&1 | tee exp61.log

import logging
from pathlib import Path
from sb.sb import Sb

apps_dir = Path('/home/ec2-user')
apps = [
    'faas-migration/Event-Processing/Lambda/event_processing_benchmark.py'
    # 'faas-migration/ThumbnailGenerator/Lambda/thumbnail_benchmark.py'
]
app_paths = [(apps_dir / a).resolve() for a in apps]
sb_clis = [Sb(p, log_level='DEBUG', debug=True) for p in app_paths]

patterns_dir = Path('/home/ec2-user/1h_very_high')
patterns = [
    'constant_1h.csv',
    'bursty_1h.csv'
]
pattern_paths = [(patterns_dir / a).resolve() for a in patterns]

def run_test(sb, trace):
    try:
        sb.prepare()
        sb.config.set('label', 'exp61.py')
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
