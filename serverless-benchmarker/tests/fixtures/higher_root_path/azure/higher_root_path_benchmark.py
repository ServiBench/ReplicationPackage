import logging
import subprocess

BENCHMARK_CONFIG = """
higher_root_path_benchmark:
  description: Example of an application that uses a higher root path \
to access shared resources among different providers.
  provider: azure
  root: ..
"""


def prepare(spec):
    # Local context
    spec['pwd'] = subprocess.getoutput('pwd')
    spec['parent_pwd'] = subprocess.getoutput('cd .. && pwd')
    # Docker context
    spec['run_pwd'] = spec.run('pwd').rstrip()
    spec['run_parent_pwd'] = spec.run('cd .. && pwd').rstrip()
    spec['content'] = spec.run('cat ../shared/content.txt').rstrip()


def invoke(spec):
    logging.info(f"retrieving content={spec['content']}")


def cleanup(spec):
    logging.info('sample cleanup')
