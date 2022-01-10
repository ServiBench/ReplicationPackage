"""Simple hello world Nodejs example based on the serverless pattern:
Amazon API Gateway to AWS Lambda: https://serverlessland.com/patterns/apigw-lambda-cdk
Source: https://github.com/aws-samples/serverless-patterns/tree/main/apigw-lambda-cdk
"""

import logging
import json
import os


BENCHMARK_CONFIG = """
apigw_node:
  description: Simple Nodejs Lambda function
  provider: aws
  region: us-east-1
  memory_size: 1024
"""


CDK_IMAGE = 'node-cdk-apigw-node'
# Manual flag to bootstrap CDK. Optionally disable after first run.
BOOTSTRAP_CDK = True


def prepare(spec):
    spec.build(CDK_IMAGE)
    spec.run('npm install', image=CDK_IMAGE)
    # Only required once per region: https://docs.aws.amazon.com/cdk/latest/guide/bootstrapping.html
    # No automated cleanup: https://github.com/aws/aws-cdk/issues/986
    if BOOTSTRAP_CDK:
        spec['account_id'] = spec.run('aws sts get-caller-identity --query Account --output text', image='aws_cli').strip()
        bootstrap_cmd = f"cdk bootstrap aws://{spec['account_id']}/{spec['region']}"
        spec.run(bootstrap_cmd, image=CDK_IMAGE)
    spec.run(f"AWS_REGION={spec['region']} MEMORY_SIZE={spec['memory_size']} cdk deploy --require-approval never --outputs-file outputs.json", image=CDK_IMAGE)
    with open('outputs.json') as f:
        outputs = json.load(f)
        spec['endpoint'] = outputs['ServerlessLandApi']['ServerlessLandEndpointC36EEEC4']
        logging.info(f"service endpoint={spec['endpoint']}")


def invoke(spec):
    envs = {
        'URL': spec['endpoint']
    }
    spec.run_k6(envs)
    # Alternative invocation through curl:
    # spec.run(invoke_curl_cmd(spec['endpoint']), image='curlimages/curl:7.80.0')


def invoke_curl_cmd(url):
    return f"""curl "{url}my/path" --verbose"""


def cleanup(spec):
    spec.run('cdk destroy --force', image=CDK_IMAGE)
