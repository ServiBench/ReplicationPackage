import logging
import json

BENCHMARK_CONFIG = """
aws_pulumi_benchmark:
  provider:
  - aws
  - pulumi
"""


def prepare(spec):
    check_aws(spec)
    check_pulumi(spec)


def check_aws(spec):
    aws = spec.run('aws sts get-caller-identity', image='aws_cli')
    aws_json = json.loads(aws)
    arn = aws_json['Arn']
    logging.info(f"aws={arn}")
    assert arn.startswith('arn:aws')


def check_pulumi(spec):
    pulumi = spec.run('pulumi whoami', image='pulumi_cli')
    assert pulumi


def invoke(spec):
    pass


def cleanup(spec):
    pass
