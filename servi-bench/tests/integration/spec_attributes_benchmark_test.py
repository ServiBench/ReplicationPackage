from pathlib import Path
import pytest
from sb.sb import Sb

tests_path = Path(__file__).parent.parent
sub_path = 'fixtures/spec_attributes/spec_attributes_benchmark.py'
bench_file = (tests_path / sub_path).resolve()


@pytest.fixture
def sb():
    return Sb(bench_file, log_level='DEBUG', debug=True)


def test_attribute_passing(sb):
    sb.test()
    assert sb.bench.spec['invoke_key'] == 'invoke_value'


@pytest.mark.local
def test_attribute_passing_local(sb):
    """Should succeed everywhere as attribute passing needs no dependencies."""
    sb.local = True
    sb.test()


@pytest.mark.docker
def test_attribute_passing_docker(sb):
    sb.docker = True
    sb.test()


def test_stepwise_attribute_passing(sb):
    assert sb.bench.spec['static_key'] == 'static_value'
    sb.prepare()
    assert sb.bench.spec['prepare_key'] == 'prepare_value'
    sb.invoke()
    assert sb.bench.spec['invoke_key'] == 'invoke_value'
    sb.cleanup()
