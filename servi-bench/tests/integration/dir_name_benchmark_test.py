from pathlib import Path
import subprocess
import platform
import pytest
from sb.sb import Sb

tests_path = Path(__file__).parent.parent
sub_path = 'fixtures/dir_name/dir_name_benchmark.py'
bench_file = (tests_path / sub_path).resolve()


@pytest.fixture
def sb():
    return Sb(bench_file, debug=True, log_level='DEBUG')


@pytest.mark.skipif(platform.system() == 'Windows',
                    reason="shell pwd command incompatible for local Windows execution")
def test_basic_pwd_dir_name(sb):
    sb.test()
    assert sb.bench.spec['run_pwd'] == '/apps/dir_name'


@pytest.mark.cli
@pytest.mark.skipif(platform.system() == 'Windows',
                    reason="shell pwd command incompatible for local Windows execution")
def test_basic_pwd_dir_name_cli():
    cmd = f"sb test --file='{bench_file}' --debug=True"
    subprocess.run(cmd, shell=True, check=True)


@pytest.mark.docker
def test_basic_pwd_dir_name_docker(sb):
    sb.docker = True
    sb.test()
