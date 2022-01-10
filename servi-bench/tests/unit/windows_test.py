from pathlib import PurePosixPath, PureWindowsPath
import pytest
from sb.benchmark_spec import BenchmarkSpec, win_vol

win_path = r'C:\Users\anonymous\serverless-benchmarker\tests\fixtures\mock_benchmark'


@pytest.fixture
def spec():
    config = {
        'empty_benchmark': {},
        'sb': {
            'host_path': win_path,
            'host_system': 'Windows'
        }
    }
    return BenchmarkSpec(config)


def test_win_vol():
    path = PureWindowsPath(r"C:\Users\anonymous\Projects")
    assert win_vol(path) == "/C/Users/anonymous/Projects"


def test_win_vol_posix():
    path = PurePosixPath('/Users/anonymous/Projects')
    assert win_vol(path) == path


def test_host_path(spec):
    assert type(spec.host_path()) == PureWindowsPath
    assert str(spec.host_path()) == win_path


def test_sub_path(spec):
    assert str(spec.sub_path()) == 'mock_benchmark'


def test_sub_path_with_root(spec):
    spec['root'] = '../..'
    assert str(spec.sub_path()) == 'tests/fixtures/mock_benchmark'
