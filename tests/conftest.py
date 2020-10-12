import os

import numpy as np
import pytest
from click.testing import CliRunner

import vpype as vp


def random_line(length: int) -> np.ndarray:
    return np.random.rand(length) + 1j * np.random.rand(length)


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


@pytest.fixture(scope="session")
def root_directory(request):
    return str(request.config.rootdir)


@pytest.fixture
def config_manager():
    return vp.ConfigManager()


@pytest.fixture(scope="session")
def config_file_factory(tmpdir_factory):
    def _make_config_file(text: str) -> str:
        path = os.path.join(tmpdir_factory.mktemp("config_file"), "config.toml")
        with open(path, "w") as fp:
            fp.write(text)
        return path

    return _make_config_file
