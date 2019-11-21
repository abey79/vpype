import pytest
from click.testing import CliRunner
import numpy as np


def random_line(length: int) -> np.ndarray:
    return np.random.rand(length) + 1j * np.random.rand(length)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(scope="session")
def root_directory(request):
    return str(request.config.rootdir)
