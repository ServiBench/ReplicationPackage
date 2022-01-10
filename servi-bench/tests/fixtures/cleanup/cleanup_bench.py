BENCHMARK_CONFIG = """
cleanup_bench:
  description: Cleanup should not abort on failure
"""


def prepare(spec):
    spec.run('false')
    spec.run('true')


def invoke(spec):
    pass


def cleanup(spec):
    spec.run('false')
    spec.run('true')
