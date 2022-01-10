from pathlib import Path
import subprocess
import pytest
import platform
from sb.sb import Sb

tests_path = Path(__file__).parent.parent
sub_path = 'fixtures/higher_root_path/azure/higher_root_path_benchmark.py'
bench_file = (tests_path / sub_path).resolve()


@pytest.fixture
def sb():
    return Sb(bench_file, log_level='DEBUG', debug=True)


@pytest.mark.skipif(platform.system() == 'Windows',
                    reason="shell pwd command incompatible for local Windows execution")
def test_benchmark_file_detect_sb():
    cmd = f"cd '{bench_file.parent}' && sb prepare cleanup --debug=True"
    subprocess.run(cmd, shell=True, check=True)


@pytest.mark.skipif(platform.system() == 'Windows',
                    reason="shell pwd command incompatible for local Windows execution")
def test_higher_root_path(sb):
    """Test the higher root path benchmark locally.
    Only works if all dependencies are configured locally.
    """
    sb.test()
    # Local context
    pwd = bench_file.parent
    assert sb.bench.spec['pwd'] == str(pwd.resolve())
    assert sb.bench.spec['parent_pwd'] == str(pwd.parent.resolve())
    assert_run_context(sb.bench.spec)


def assert_run_context(spec):
    assert spec['run_pwd'] == '/apps/higher_root_path/azure'
    assert spec['run_parent_pwd'] == '/apps/higher_root_path'
    assert spec['content'] == 'sample_content'


@pytest.mark.docker
def test_higher_root_path_docker(sb):
    sb.docker = True
    sb.test()
    # Docker context
    # MAYBE: implement support for programmatic invocation using Docker context
    # Currently, the execution finishes in the Docker context and its results
    # are not available in this outer host context. To support this feature,
    # there needs to be a mechanism that signals invocation via host context
    # and does not delete the config file upon completion. Additionally,
    # the run_in_docker methods need to reload the configuration upon completion
    # and properly clean it up in the host context.
    # assert sb.bench.spec['pwd'] == '/apps/higher_root_path/azure'
    # assert sb.bench.spec['parent_pwd'] == '/apps/higher_root_path'
    # assert_run_context(sb.bench.spec)
