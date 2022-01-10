from pathlib import Path
import subprocess
import pytest
from sb.sb import Sb

tests_path = Path(__file__).parent.parent
sub_path = 'fixtures/empty/empty_benchmark.py'
bench_file = (tests_path / sub_path).resolve()


@pytest.fixture
def sb():
    return Sb(bench_file, log_level='DEBUG', debug=True)


def test_empty_benchmark_lifecycle(sb):
    sb.test()


@pytest.mark.local
def test_empty_benchmark_lifecycle_local(sb):
    """Should succeed everywhere as the empty benchmark needs no dependencies."""
    sb.local = True
    sb.test()


@pytest.mark.docker
def test_empty_benchmark_lifecycle_docker(sb):
    sb.docker = True
    sb.test()


@pytest.mark.cli
def test_invoke_cli_without_config():
    """Checks that invoke can be called without an existing config (i.e., without prepare)"""
    cmd = f"sb invoke single cleanup --file='{bench_file}' --debug=True"
    subprocess.run(cmd, shell=True, check=True)
