BENCHMARK_CONFIG = """
file_permissions_benchmark:
  provider: aws
"""
TAG = 'sb-file-permissions-test'


def prepare(spec):
    spec.build(TAG)
    spec.run("echo 'test_content' > test.txt", image=TAG)


def invoke(spec):
    spec['file'] = spec.run('cat test.txt').rstrip()


def cleanup(spec):
    spec.run("rm test.txt")
