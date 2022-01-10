BENCHMARK_CONFIG = """
ibm_benchmark:
  provider: ibm
"""


def prepare(spec):
    check_ibm(spec)


def check_ibm(spec):
    ibm = spec.run('ibmcloud regions', image='ibm_cli')
    assert ibm.startswith('Listing regions...')
    # MAYBE: Add extra check after setting region, API endpoint, organization, and space


def invoke(spec):
    pass


def cleanup(spec):
    pass
