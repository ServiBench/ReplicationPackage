from pathlib import Path
import pytest
from sb.sb import Sb

tests_path = Path(__file__).parent.parent
sub_path = 'fixtures/empty/empty_benchmark.py'
bench_file = (tests_path / sub_path).resolve()


@pytest.fixture
def sb():
    return Sb(bench_file, log_level='DEBUG', debug=True)


def test_dollar_sign(sb):
    spec = sb.bench.spec
    cmd = "echo '  POST - https://abcdef1234.execute-api.us-east-1.amazonaws.com/production/upload' | awk '{print $3}'"  # noqa: E501
    out = spec.run(cmd).rstrip()
    assert out == 'https://abcdef1234.execute-api.us-east-1.amazonaws.com/production/upload'


@pytest.mark.docker
def test_dollar_sign_docker(sb):
    sb.docker = True
    spec = sb.bench.spec
    cmd = "echo '  POST - https://abcdef1234.execute-api.us-east-1.amazonaws.com/production/upload' | awk '{print $3}'"  # noqa: E501
    out = spec.run(cmd).rstrip()
    assert out == 'https://abcdef1234.execute-api.us-east-1.amazonaws.com/production/upload'
