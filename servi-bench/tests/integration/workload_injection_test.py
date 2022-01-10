from pathlib import Path
from sb.benchmark import SB_CONFIG, SB_DIR
from sb.benchmark_spec import BenchmarkSpec
import pytest
from sb.sb import Sb

tests_path = Path(__file__).parent.parent
sub_path = 'fixtures/empty/empty_benchmark.py'
bench_file = (tests_path / sub_path).resolve()
sb_config_dir = bench_file.parent / SB_DIR / SB_CONFIG
workload_file = bench_file.parent / BenchmarkSpec.DEFAULT_OPTIONS


@pytest.fixture
def sb():
    # Remove potential config leftovers before each test
    if sb_config_dir.exists():
        sb_config_dir.unlink()
    if workload_file.exists():
        workload_file.unlink()
    return Sb(bench_file, log_level='DEBUG', debug=True)


def test_inject_numeric_workload(sb):
    sb.invoke(10)
    assert workload_file.read_text() == '{"vus": 1, "iterations": 10}'
