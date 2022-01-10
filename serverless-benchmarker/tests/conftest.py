from pathlib import Path
import logging
import shutil

tests_dir = Path(__file__).parent
fixtures_dir = tests_dir.joinpath('fixtures')


def pytest_sessionstart(session):
    patterns = ['**/logs', '**/.sb', '**/workload_options.json']
    print(f"Delete the following files and directories in test fixtures: {patterns}")
    for pattern in patterns:
        for file in fixtures_dir.glob(pattern):
            path = Path(file)
            if path.is_file():
                logging.debug(f"rm-file:{path}")
                path.unlink()
            else:
                logging.debug(f"rm-dir:{path}")
                shutil.rmtree(path)
