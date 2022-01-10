from pathlib import Path
import pytest
from sb.sb import Sb

# Skip all credentials tests because secrets are not available in CI environment
# Only run in trusted environments because the logs may leak credentials!
pytestmark = pytest.mark.skip('all credentials test only work when secrets are provided')


@pytest.fixture
def sb(provider='aws'):
    tests_path = Path(__file__).parent.parent
    sub_path = f"fixtures/credentials/{provider}_benchmark.py"
    bench_file = (tests_path / sub_path).resolve()
    return Sb(bench_file, log_level='DEBUG', debug=True)


@pytest.mark.parametrize('sb', ['aws', 'azure', 'google', 'ibm'], indirect=True)
def test_credentials(sb):
    sb.prepare()


@pytest.mark.parametrize('sb', ['aws_pulumi'], indirect=True)
def test_multiple_credentials(sb):
    sb.prepare()
