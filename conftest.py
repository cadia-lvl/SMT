import pytest
from glob import glob
from corpus import pipeline_load

def pytest_addoption(parser):
    parser.addoption(
        "--data", action="store", default="type1", help="Full path to data dir"
    )


@pytest.fixture
def data_dir(request):
    return request.config.getoption("--data")


@pytest.fixture
def glob_files(request):
    data_dir = request.config.getoption("--data")

    def glob_pattern(pattern):
        return glob(f'{data_dir}/{pattern}')

    return glob_pattern


@pytest.fixture
def get_pipeline(request):
    data_dir = request.config.getoption("--data")

    def load_pipeline(stages):
        return pipeline_load(data_dir, stages)

    return load_pipeline
