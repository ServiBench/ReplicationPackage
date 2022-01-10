import logging
import json
import random

BENCHMARK_CONFIG = """
matrix_multiplication:
  description: Parallel matrix multiplication workflow.
  provider: aws
  region: us-east-1
  memory_size: 1024
  stage: dev
  root: ..
"""
BUILD_IMAGE = 'dotnet5-lambda-tools'

def prepare(spec):
    # The deploy_id is used to generate globally unique S3 bucket names
    spec['deploy_id'] = spec['deploy_id'] or random.randint(1000, 9999)
    spec['data_bucket_name'] = f"matrix-multiplication-data-sb-{spec['deploy_id']}"
    spec.build(BUILD_IMAGE)
    build_cmd = 'export PATH="$PATH:/root/.dotnet/tools"; dotnet-lambda package --configuration release --framework netcoreapp3.1 --output-package bin/release/netcoreapp3.1/matrix-mul.zip'
    spec.run(build_cmd, image=BUILD_IMAGE)
    spec.run('npm install', image='serverless_cli')
    spec.run(sls_cmd('deploy', spec), image='serverless_cli')
    spec['endpoint'] = spec.run(sls_cmd('info', spec) + " | grep ServiceEndpoint | awk '{print $2}'", image='serverless_cli').rstrip()
    logging.info(f"endpoint={spec['endpoint']}")


def invoke(spec):
    url = f"{spec['endpoint']}/run"
    body = json.dumps({
        "MatrixSize": 50,
        "MaxValue": 100,
        "Seed": 123321
    })
    envs = {
        'URL': url,
        'BODY': body
    }
    spec.run_k6(envs)


def cleanup(spec):
    spec.run(f"aws s3 rm s3://{spec['data_bucket_name']}/ --recursive", image='aws_cli')
    spec.run(sls_cmd('remove', spec), image='serverless_cli')


def sls_cmd(command, spec):
    """Returns a shell command string for a given Serverless Framework `command` in the given `spec` context.
    Configures environment variables (envs)."""
    envs = (
        f"STAGE={spec['stage']} "
        f"REGION={spec['region']} "
        f"MEMORY_SIZE={spec['memory_size']} "
        f"DATA_BUCKET_NAME={spec['data_bucket_name']} "
    )
    return f"{envs}serverless {command} --verbose"
