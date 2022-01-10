import logging
import json
import random

BENCHMARK_CONFIG = """
video_processing:
  description: Converts a color MP4 video to grayscale AVI.
  provider: aws
  stage: dev
  region: us-east-1
  memory_size: 1024
  root: ..
  data_replication: 1
  object_key: vid1.mp4
"""

PY_BUILD_SLS = 'python-build-opencv-with-serverless'

def prepare(spec):
    spec['deploy_id'] = spec['deploy_id'] or random.randint(1000, 9999)

    spec.build(PY_BUILD_SLS)
    spec.run(f"npm install", image=PY_BUILD_SLS)

    #create the dataset and model buckets
    spec.run(f"aws s3 mb s3://{input_bucket(spec)} --region={spec['region']}", image=PY_BUILD_SLS)
    spec.run(f"aws s3 mb s3://{output_bucket(spec)} --region={spec['region']}", image=PY_BUILD_SLS)

    #create dataset copies inside dataset_bucket
    obj_key_splitted = spec['object_key'].split('.')
    obj_key_prefix = obj_key_splitted[0] #e.g., vid1
    obj_key_suffix = obj_key_splitted[1] #e.g., mp4

    for data_number in range(0, spec['data_replication']):
        if data_number == 0: #upload it from local only once
            spec.run(f"aws s3 cp ./test_video/{spec['object_key']} s3://{input_bucket(spec)}/{obj_key_prefix}-{data_number}.{obj_key_suffix}", image=PY_BUILD_SLS)
        else: #create the copies within the S3 bucket
            spec.run(f"aws s3 cp s3://{input_bucket(spec)}/{obj_key_prefix}-0.{obj_key_suffix} s3://{input_bucket(spec)}/{obj_key_prefix}-{data_number}.{obj_key_suffix}", image=PY_BUILD_SLS)
    #deploy lambda function    
    spec.run(sls_cmd('deploy', spec), image=PY_BUILD_SLS)
    spec['endpoint'] = spec.run(sls_cmd('info', spec) + " | grep ServiceEndpoint | awk '{print $2}'", image=PY_BUILD_SLS).rstrip()
    logging.info(f"endpoint={spec['endpoint']}")


def invoke(spec): 
    url = f"{spec['endpoint']}/process"
    body_json = { 
        "input_bucket": input_bucket(spec), 
        "object_key": spec['object_key'], 
        "output_bucket": output_bucket(spec) 
    }
    body = json.dumps(body_json)
    envs = {
        'URL': url,
        'BODY': body,
        'DATA_REPLICATION': spec['data_replication'],
        'OBJECT_KEY': spec['object_key']
    }
    spec.run_k6(envs)


def cleanup(spec): 
    logging.info('cleanup(): delete all functions and resources (e.g., test files or databases)')
    spec.run(f"aws s3 rb s3://{input_bucket(spec)} --force", image=PY_BUILD_SLS)
    spec.run(f"aws s3 rb s3://{output_bucket(spec)} --force", image=PY_BUILD_SLS)
    spec.run(sls_cmd('remove', spec), image=PY_BUILD_SLS) #delete deployment


def sls_cmd(command, spec):
    """Returns a shell command string for a given Serverless Framework `command` in the given `spec` context.
    Configures environment variables (envs)."""
    envs = (
        f"STAGE={spec['stage']} "
        f"REGION={spec['region']} "
        f"MEMORY_SIZE={spec['memory_size']} "
    )
    return f"{envs}serverless {command} --verbose"


def input_bucket(spec):
    return f"video-processing-input-{spec['deploy_id']}"


def output_bucket(spec):
    return f"video-processing-output-{spec['deploy_id']}"
