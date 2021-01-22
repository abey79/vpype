import os
from typing import Callable

import numpy as np
import pytest
from click.testing import CliRunner
from PIL import Image

import vpype as vp


def random_line(length: int) -> np.ndarray:
    return np.random.rand(length) + 1j * np.random.rand(length)


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


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


# IMAGE COMPARE SUPPORT

REFERENCE_IMAGES_DIR = (
    os.path.dirname(__file__) + os.path.sep + "data" + os.path.sep + "baseline"
)


def pytest_addoption(parser):
    parser.addoption(
        "--store-ref-images",
        action="store_true",
        help="Write reference image for assert_image_similarity().",
    )


@pytest.fixture
def assert_image_similarity(request) -> Callable:
    store_ref_image = request.config.getoption("--store-ref-images")
    test_id = request.node.name
    test_id = test_id.replace("[", "-").replace("]", "-").replace("/", "_").rstrip("-")
    path = REFERENCE_IMAGES_DIR + os.path.sep + test_id + ".png"

    def _assert_image_similarity(img: Image) -> None:
        if store_ref_image:
            img.save(path)
        else:
            try:
                ref_img = Image.open(path)
            except FileNotFoundError:
                pytest.fail(f"reference image {path} not found")
                return

            img = img.convert(ref_img.mode)
            img = img.resize(ref_img.size)
            sum_sq_diff = np.sum(
                (np.asarray(ref_img).astype("float") - np.asarray(img).astype("float")) ** 2
            )

            if sum_sq_diff != 0:
                normalized_sum_sq_diff = sum_sq_diff / np.sqrt(sum_sq_diff)
                if normalized_sum_sq_diff > 0.001:
                    pytest.fail("image similarity test failed")

    return _assert_image_similarity
