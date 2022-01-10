from pathlib import Path
import platform
from sb.benchmark_spec import BenchmarkSpec

tests_path = Path(__file__).parent.parent
sub_path = 'fixtures/higher_root_path/azure/higher_root_path_benchmark.py'
bench_file = (tests_path / sub_path).resolve()


def test_root_path():
    config = {
        'my_bench': {
            'root': '..'
        },
        'sb': {
            'host_path': str(bench_file.parent),
            'host_system': platform.system()
        }
    }
    spec = BenchmarkSpec(config)
    assert spec.host_root_path() == bench_file.parent.parent


def test_no_root_path():
    config = {
        'no_root_bench': {},
        'sb': {
            'host_path': str(bench_file.parent),
            'host_system': platform.system()
        }
    }
    spec = BenchmarkSpec(config)
    assert spec.host_root_path() == bench_file.parent


def test_sub_path():
    config = {
        'my_bench': {
            'root': '..'
        },
        'sb': {
            'host_path': str(bench_file.parent),
            'host_system': platform.system()
        }
    }
    spec = BenchmarkSpec(config)
    assert str(spec.sub_path()) == 'higher_root_path/azure'


def test_getitem():
    config = {
        'sample_benchmark': {
            'provider': 'aws'
        }
    }
    spec = BenchmarkSpec(config)
    assert spec['provider'] == 'aws'


def test_setitem():
    config = {
        'my_benchmark': {}
    }
    spec = BenchmarkSpec(config)
    spec['endpoint'] = 'https://my-function.com'
    assert spec['endpoint'] == 'https://my-function.com'
