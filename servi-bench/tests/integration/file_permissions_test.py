from pathlib import Path
import subprocess
import pytest
from sb.sb import Sb

tests_path = Path(__file__).parent.parent
sub_path = 'fixtures/file_permissions/file_permissions_benchmark.py'
bench_file = (tests_path / sub_path).resolve()


"""Aims to verify file permissions such that file I/O operations succeed
in mounted directories.
"""


@pytest.fixture
def sb():
    return Sb(bench_file, debug=True, log_level='DEBUG')


def test_file_permissions(sb):
    sb.test()
    assert sb.bench.spec['file'] == 'test_content'


@pytest.mark.cli
def test_file_permissions_cli():
    cmd = f"sb test --file='{bench_file}' --debug=True"
    subprocess.run(cmd, shell=True, check=True)


@pytest.mark.docker
def test_file_permissions_docker(sb):
    sb.docker = True
    sb.test()
