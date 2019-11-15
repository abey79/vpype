import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(scope="session")
def root_directory(request):
    return str(request.config.rootdir)
