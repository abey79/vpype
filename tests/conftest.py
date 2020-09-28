import numpy as np
import pytest
from click.testing import CliRunner

import vpype as vp


def random_line(length: int) -> np.ndarray:
    return np.random.rand(length) + 1j * np.random.rand(length)


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture(scope="session")
def root_directory(request):
    return str(request.config.rootdir)


@pytest.fixture
def config_manager():
    return vp.ConfigManager()


@pytest.fixture(scope="session")
def config_file_factory(tmp_path_factory):
    def _make_config_file(text: str) -> str:
        path = tmp_path_factory.mktemp("config_file") / "config.toml"
        path.write_text(text)
        return str(path)

    return _make_config_file
