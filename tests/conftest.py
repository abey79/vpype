import os
import pathlib
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
# ideally, this would be cleanly factored into a pytest plug-in akin to pytest-mpl

REFERENCE_IMAGES_DIR = (
    os.path.dirname(__file__) + os.path.sep + "data" + os.path.sep + "baseline"
)


def pytest_addoption(parser):
    parser.addoption(
        "--store-ref-images",
        action="store_true",
        help="Write reference image for assert_image_similarity().",
    )

    parser.addoption(
        "--skip-image-similarity",
        action="store_true",
        help="Skip tests using assert_image_similarity().",
    )


def write_image_similarity_fail_report(
    image: Image,
    reference_image: Image,
    image_array: np.ndarray,
    reference_image_array: np.ndarray,
    test_id: str,
    diff: float,
) -> None:
    report_dir = pathlib.Path.cwd() / "test_report_img_sim" / test_id
    report_dir.mkdir(parents=True, exist_ok=True)
    diff_img = Image.fromarray(np.abs(reference_image_array - image_array).astype(np.uint8))

    image.save(str(report_dir / "test_image.png"))
    reference_image.save(str(report_dir / "reference_image.png"))
    diff_img.save(str(report_dir / "difference_image.png"))
    np.save(str(report_dir / "test_image_array.npy"), image_array)
    np.save(str(report_dir / "reference_image_array.npy"), reference_image_array)
    with open(str(report_dir / "report.txt"), "w") as fp:
        fp.write(f"Test ID: {test_id}\nComputed different: {diff}")


@pytest.fixture
def assert_image_similarity(request) -> Callable:
    if request.config.getoption("--skip-image-similarity"):
        pytest.skip("image similarity test skipped (--skip-image-similarity)")

    store_ref_image = request.config.getoption("--store-ref-images")
    test_id = request.node.name
    test_id = test_id.replace("[", "-").replace("]", "-").replace("/", "_").rstrip("-")
    path = REFERENCE_IMAGES_DIR + os.path.sep + test_id + ".png"

    def _assert_image_similarity(img: Image) -> None:
        nonlocal store_ref_image, test_id, path

        if store_ref_image:  # pragma: no cover
            img.save(path)
            pytest.skip("storing reference images")
        else:
            try:
                ref_img = Image.open(path)
            except FileNotFoundError:
                pytest.fail(f"reference image {path} not found")
                return

            img = img.convert(ref_img.mode)
            img = img.resize(ref_img.size)
            ref_img_arr = np.asarray(ref_img).astype("float")
            img_arr = np.asarray(img).astype("float")
            sum_sq_diff = np.mean((ref_img_arr - img_arr) ** 2)

            if sum_sq_diff != 0:
                normalized_sum_sq_diff = sum_sq_diff / np.sqrt(sum_sq_diff)
                if normalized_sum_sq_diff > 5.5:  # pragma: no cover
                    write_image_similarity_fail_report(
                        img, ref_img, img_arr, ref_img_arr, test_id, normalized_sum_sq_diff
                    )
                    pytest.fail(
                        f"image similarity test failed (rms: {normalized_sum_sq_diff})"
                    )

    return _assert_image_similarity
