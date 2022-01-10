from pathlib import Path
import pytest
from sb.sb import Sb

tests_path = Path(__file__).parent.parent
sub_path = 'fixtures/cleanup/cleanup_bench.py'
bench_file = (tests_path / sub_path).resolve()


@pytest.fixture
def sb():
    return Sb(bench_file, log_level='DEBUG', debug=True)


def test_check_on_prepare(sb):
    """spec.run() commands should fail on non-zero exit status by default."""
    exception_msg = r"The spec.run\(\) command `false` exited unsuccessfully\..*"
    with pytest.raises(Exception, match=exception_msg):
        sb.prepare()


def test_no_check_on_cleanup(sb):
    """All cleanup commands should be executed even if some spec.run commands fail"""
    sb.cleanup()
