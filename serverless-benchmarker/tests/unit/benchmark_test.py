from pathlib import Path
from sb.benchmark import Benchmark

tests_path = Path(__file__).parent.parent
sub_path = 'fixtures/higher_root_path/azure/higher_root_path_benchmark.py'
bench_file = (tests_path / sub_path).resolve()


def test_config_path():
    bench = Benchmark(None, bench_file)
    config_path = (bench_file.parent / '.sb/config.yml')
    assert bench.config_path() == config_path
