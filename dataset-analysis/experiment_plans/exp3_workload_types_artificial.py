#!/usr/bin/env python

"""Artificial workload types
Runs an experiment with two extreme load types with the same average invocation rate:
* on_off: extreme bursts followed by a few seconds break
* constant: baseline load using a constant arrival rate
"""

# Usage:
# 1) Open tmux
# 2) Activate virtualenv
# 3) Run ./exp3_workload_types_artificial.py 2>&1 | tee -a exp3_workload_types_artificial.log

import logging
from pathlib import Path
from sb.sb import Sb

apps_dir = Path('/home/ec2-user')
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

seconds_per_target = 5*60

def on_off_options(load_level):
    """Returns k6 workload options for an on_off workload
    with extreme bursts given an average load level.
    """
    # Load level (rps)
    # Determine the average load in requests per second
    targets = [load_level]

    # generate custom options
    stages = []
    # Determine fraction on vs off. Examples:
    # * 2 every second => 1 on, 1 off
    # * 4 every 4th second => 1 on, 3 off
    # * 5 every 5th second => 1 on, 4 off
    on_off_fraction = 4
    for target in targets:
        # Generate max variability pattern with 1ms transition
        for tick in range(seconds_per_target):
            tick_target = 0
            if tick % on_off_fraction == 0:
                tick_target = target * on_off_fraction
            stages.append({
                'target': tick_target,
                'duration': '1ms'
            })
            stages.append({
                'target': tick_target,
                'duration': '999ms'
            })

    start_rate = targets[0]
    pre_allocated_vus = max(round(start_rate * on_off_fraction / 2), 500)
    options = {
        "scenarios": {
            "benchmark_scenario": {
                "executor": "ramping-arrival-rate",
                "startRate": start_rate,
                "timeUnit": "1s",
                "preAllocatedVUs": pre_allocated_vus,
                "stages": stages
            }
        }
    }
    return options


def constant_options(load_level):
    """Returns k6 workload options for a constant workload
    that maintains a constant arrival rate for a given time.
    """
    # Load level (rps)
    targets = [load_level]

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
    return options

# Draft for adding patterns later:
# patterns_dir = Path('/home/ec2-user/20min_20rps')
# patterns = [
#     'steady.csv',
#     'fluctuating.csv',
#     'jump.csv',
#     'spikes.csv'
# ]
# pattern_paths = [(patterns_dir / a).resolve() for a in patterns]

# Alternative simpler implementation but:
# a) not supported by current analysis script
# b) created slightly more load on average 11 instead of 10 compared to
#    10.26 by the default ramping-arrival-time-approach
# c) Don't know whether there's a limit for number of scenarios they
#    are all displayed with timers during execution
# However, it appeared that constant-arrival-rate can generate ramp-up slightly faster
# scenarios = dict()
# for i in range(round(seconds_per_target / on_off_fraction)):
#     scenario = {
#         "executor": "constant-arrival-rate",
#         "rate": load_level * on_off_fraction,
#         "timeUnit": "1s",
#         "duration": "1s",
#         "preAllocatedVUs": load_level * on_off_fraction,
#         "startTime": f"{i*on_off_fraction}s"
#     }
#     scenarios[f"on{i}"] = scenario

# options = {
#     "scenarios": {
#         **scenarios
#     }
# }

def run_test(sb, load_level):
    ## On_off workload choice
    # options = on_off_options(load_level)
    # workload_label = 'on_off'
    ## Constant workload choice
    options = constant_options(load_level)
    workload_label = 'constant'
    ## Derive label
    exp_label = f"exp3_workload_types_{workload_label}"
    try:
        sb.prepare()
        sb.config.set('label', exp_label)
        sb.config.set('load_level', load_level)
        sb.config.set('workload_label', workload_label)
        sb.wait(30)
        sb.invoke('custom', workload_options=options)
        sb.wait(5*60)
        sb.get_traces()
    except:
        logging.error('Error during execution of benchmark. Cleaning up ...')
    finally:
        sb.cleanup()

# run all
for sb, load_level in sb_clis:
    run_test(sb, load_level)
