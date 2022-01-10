BENCHMARK_CONFIG = """
google_benchmark:
  provider: google
"""


def prepare(spec):
    check_google(spec)


def check_google(spec):
    # MAYBE: find other sensible login check that doesn't print an access token
    # For example: https://cloud.google.com/sdk/gcloud/reference/auth/list
    google = spec.run('gcloud auth print-access-token', image='google_cli')
    assert '' != google.strip()


def invoke(spec):
    pass


def cleanup(spec):
    pass
