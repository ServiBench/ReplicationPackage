BENCHMARK_CONFIG = """
spec_attributes_benchmark:
  description: Testcase for attribute passing between stages.
  static_key: static_value
"""


def prepare(spec):
    assert spec['static_key'] == 'static_value'
    spec['prepare_key'] = 'prepare_value'


def invoke(spec):
    assert spec['prepare_key'] == 'prepare_value'
    spec['invoke_key'] = 'invoke_value'
    # overwrite static key
    spec['static_key'] = 'new_static_value'


def cleanup(spec):
    assert spec['prepare_key'] == 'prepare_value'
    # static values in the BENCHMARK_CONFIG take precedence
    # over dynamic values and overwrite them upon reload
    spec['static_key'] = 'static_value'
