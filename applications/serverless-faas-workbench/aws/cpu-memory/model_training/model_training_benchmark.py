import logging
import json
import random 

BENCHMARK_CONFIG = """
model_training:
  description: Trains a model on Amazon reviews dataset.
  provider: aws
  stage: dev
  region: us-east-1
  memory_size: 1024
  data_replication: 1
  data_object_key: reviews10mb.csv
  model_object_key: lr_model.pk
"""

# Python build image for cross-compiling native code and runtime dependencies
# with the Serverless framework for using the Python requirements plugin:
# https://www.serverless.com/plugins/serverless-python-requirements
PY_BUILD_SLS = 'python-build-scikit-with-serverless'

def prepare(spec):
    spec['deploy_id'] = spec['deploy_id'] or random.randint(1000, 9999)

    spec.build(PY_BUILD_SLS)
    spec.run(f"npm install", image=PY_BUILD_SLS)

    #create the dataset and model buckets
    spec.run(f"aws s3 mb s3://{model_bucket(spec)} --region={spec['region']}", image=PY_BUILD_SLS)
    spec.run(f"aws s3 mb s3://{dataset_bucket(spec)} --region={spec['region']}", image=PY_BUILD_SLS)

    #create dataset copies inside dataset_bucket
    data_key_splitted = spec['data_object_key'].split('.')
    data_key_prefix = data_key_splitted[0] #e.g., reviews10mb
    data_key_suffix = data_key_splitted[1] #e.g., csv
    for data_number in range(0, spec['data_replication']):
        if data_number == 0: #upload it from local only once
            spec.run(f"aws s3 cp ./test_data/{spec['data_object_key']} s3://{dataset_bucket(spec)}/{data_key_prefix}-{data_number}.{data_key_suffix}", image=PY_BUILD_SLS)
        else: #create the copies within the S3 bucket
            spec.run(f"aws s3 cp s3://{dataset_bucket(spec)}/{data_key_prefix}-0.{data_key_suffix} s3://{dataset_bucket(spec)}/{data_key_prefix}-{data_number}.{data_key_suffix}", image=PY_BUILD_SLS)
    
    #deploy lambda function
    spec.run(sls_cmd('deploy', spec), image=PY_BUILD_SLS)

    spec['endpoint'] = spec.run(sls_cmd('info', spec) + " | grep ServiceEndpoint | awk '{print $2}'", image=PY_BUILD_SLS).rstrip()
    logging.info(f"endpoint={spec['endpoint']}")


def invoke(spec):
    url = f"{spec['endpoint']}/train"
    # json object with the buckets' information
    body_json = {
        "dataset_object_key": spec['data_object_key'],
        "dataset_bucket": dataset_bucket(spec),
        "model_bucket": model_bucket(spec),
        "model_object_key": spec['model_object_key']
    }
    body = json.dumps(body_json)
    envs = {
        'URL': url,
        'BODY': body,
        'DATA_REPLICATION': spec['data_replication'],
        'DATASET_OBJECT_KEY': spec['data_object_key'],
        'MODEL_OBJECT_KEY' : spec['model_object_key']
    }
    spec.run_k6(envs)


def cleanup(spec): #delete everything that the app created including the deployment itself
    spec.run(f"aws s3 rb s3://{dataset_bucket(spec)} --force", image=PY_BUILD_SLS)
    spec.run(f"aws s3 rb s3://{model_bucket(spec)} --force", image=PY_BUILD_SLS)
    spec.run(sls_cmd('remove', spec), image=PY_BUILD_SLS)


def sls_cmd(command, spec):
    """Returns a shell command string for a given Serverless Framework `command` in the given `spec` context.
    Configures environment variables (envs)."""
    envs = (
        f"STAGE={spec['stage']} "
        f"REGION={spec['region']} "
        f"MEMORY_SIZE={spec['memory_size']} "
    )
    return f"{envs}serverless {command} --verbose"


def dataset_bucket(spec):
    return f"amazon-review10mb-data-{spec['deploy_id']}"


def model_bucket(spec):
    return f"amazon-review10mb-model-{spec['deploy_id']}"
