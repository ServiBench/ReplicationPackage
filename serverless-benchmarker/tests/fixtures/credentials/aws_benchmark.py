import logging
import json

BENCHMARK_CONFIG = """
aws_benchmark:
  provider: aws
"""


def prepare(spec):
    check_aws(spec)


def check_aws(spec):
    aws = spec.run('aws sts get-caller-identity', image='aws_cli')
    aws_json = json.loads(aws)
    arn = aws_json['Arn']
    logging.info(f"aws={arn}")
    assert arn.startswith('arn:aws')


def invoke(spec):
    pass


def cleanup(spec):
    pass
