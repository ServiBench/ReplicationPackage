import logging

BENCHMARK_CONFIG = """
todo_api:
  description: Todolist HTTP backend using DynamoDB.
  provider: aws
  region: us-east-1
  memory_size: 1024
  stage: dev
  root: ..
"""


def prepare(spec):
    spec.run('make clean build', image='golang:1.16.2')
    spec.run(sls_cmd('deploy', spec), image='serverless_cli')
    spec['endpoint'] = spec.run(sls_cmd('info', spec) + " | grep ServiceEndpoint | awk '{print $2}'", image='serverless_cli').rstrip()
    logging.info(f"service endpoint={spec['endpoint']}")


def invoke(spec):
    envs = {
        'URL': spec['endpoint']
    }
    spec.run_k6(envs)


def cleanup(spec):
    spec.run(sls_cmd('remove', spec), image='serverless_cli')


def sls_cmd(command, spec):
    """Returns a shell command string for a given Serverless Framework `command` in the given `spec` context.
    Configures environment variables (envs)."""
    envs = (
        f"STAGE={spec['stage']} "
        f"REGION={spec['region']} "
        f"MEMORY_SIZE={spec['memory_size']} "
    )
    return f"{envs}serverless {command} --verbose"
