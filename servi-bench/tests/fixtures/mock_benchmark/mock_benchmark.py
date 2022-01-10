import logging
import re
import subprocess

BENCHMARK_CONFIG = """
mock_benchmark:
  description: Illustrative mock example benchmark.
  region: us-east-1
"""


def prepare(spec):
    logging.info('prepare(): building and deploying mock benchmark')
    spec['endpoint'] = f"https://my-function.com/{spec['region']}/invoke"
    proc = subprocess.run('pwd', capture_output=True, text=True, shell=True)
    spec['pwd'] = proc.stdout.rstrip()
    out = spec.run('git --version', image='alpine/git:v2.30.1', check=True).rstrip()
    # Sample output: "git version 2.30.1"
    spec['git_version'] = out.split()[2]


def invoke(spec):
    logging.info('invoke(): invoke app a single time (via HTTP or other trigger)')
    res = re.search("https?://([A-Za-z_0-9.-]+).*", spec['endpoint'])
    domain_name = res.group(1)
    spec['result'] = domain_name
    logging.info(f"result={domain_name}")


def cleanup(spec):
    logging.info('cleanup(): delete all functions and resources (e.g., test files or databases)')
