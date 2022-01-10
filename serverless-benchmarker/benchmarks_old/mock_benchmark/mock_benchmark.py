import logging
import re
import subprocess

from timeit import default_timer as timer
import os

BENCHMARK_CONFIG = """
mock_benchmark:
  description: Illustrative mock example benchmark.
  provider: aws
  region: us-east-1
  endpoint: DYNAMIC
"""


def prepare(spec):
    logging.info('prepare(): building and deploying mock benchmark')
    spec['endpoint'] = f"https://my-function.com/{spec['region']}/invoke"
    # Executing shell commands with Python: https://janakiev.com/blog/python-shell-commands/
    # a) os.system(CMD)
    # b) subprocess.run(["ls", "-l"])
    # c) list_dir = subprocess.Popen(["ls", "-l"]); list_dir.wait()
    # Returns a byte object. Decode with: .decode("ascii") or decode("utf-8")
    spec['pwd'] = subprocess.run('pwd', shell=True, stdout=subprocess.PIPE).stdout.decode("utf-8").strip()


def invoke(spec):
    start = timer()
    logging.info('invoke(): invoke app a single time (via HTTP or other trigger)')
    result = re.search("https?://([A-Za-z_0-9.-]+).*", spec['endpoint'])
    logging.info(f"pwd={spec['pwd']}")
    # Suggestion: expose Python object for logging results or log parsing
    logging.info(f"result={result.group(1)}")
    spec.run('mvn --version', image = 'maven:3.6.3-jdk-8-slim')
    # spec.run('echo "Hello from within L2 container" >> test.txt')
    end = timer()
    logging.info(f"time={end - start}")


def cleanup(spec):
    logging.info('cleanup(): delete all functions and other created resources (e.g., test files or databases)')
