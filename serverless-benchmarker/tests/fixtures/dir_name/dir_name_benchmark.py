BENCHMARK_CONFIG = """
dir_name_benchmark:
  provider: aws
"""


def prepare(spec):
    spec['run_pwd'] = spec.run('pwd').rstrip()


def invoke(spec):
    return ''


def cleanup(spec):
    return ''
