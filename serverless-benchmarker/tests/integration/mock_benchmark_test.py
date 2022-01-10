from pathlib import Path
import subprocess
import platform
import pytest
from sb.sb import Sb

tests_path = Path(__file__).parent.parent
sub_path = 'fixtures/mock_benchmark/mock_benchmark.py'
bench_file = (tests_path / sub_path).resolve()


@pytest.fixture
def sb():
    return Sb(bench_file, log_level='DEBUG', debug=True)


@pytest.mark.skipif(platform.system() == 'Windows',
                    reason="shell pwd command incompatible for local Windows execution")
def test_mock_sample_benchmark(sb):
    sb.test()
    assert sb.bench.spec['result'] == 'my-function.com'
    assert sb.bench.spec['git_version'] == '2.30.1'


@pytest.mark.cli
@pytest.mark.skipif(platform.system() == 'Windows',
                    reason="shell pwd command incompatible for local Windows execution")
def test_mock_sample_benchmark_cli():
    cmd = f"sb test --file='{bench_file}' --debug=True"
    subprocess.run(cmd, shell=True, check=True)


@pytest.mark.cli
@pytest.mark.skipif(platform.system() == 'Windows',
                    reason="shell pwd command incompatible for local Windows execution")
def test_mock_sample_benchmark_chaining_cli():
    cmd = f"sb prepare invoke 2 cleanup --file='{bench_file}' --debug=True"
    subprocess.run(cmd, shell=True, check=True)
