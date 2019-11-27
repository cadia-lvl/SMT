from pathlib import Path
import pytest
from glob import glob

from frontend.bulk import list_dir


def pytest_addoption(parser):
    parser.addoption(
        "--data", action="store", default="type1", help="Full path to data dir"
    )


@pytest.fixture
def data_dir(request):
    return Path(request.config.getoption("--data"))


@pytest.fixture
def glob_files(request):
    data_dir = request.config.getoption("--data")

    def glob_pattern(pattern):
        return glob(f'{data_dir}/{pattern}')

    return glob_pattern


@pytest.fixture
def list_data_dir(request):
    data_dir = request.config.getoption("--data")

    def load_pipeline(langs, stages=None):
        if stages:
            return list_dir(Path(data_dir), langs, stages)
        return list_dir(Path(data_dir), langs)

    return load_pipeline
