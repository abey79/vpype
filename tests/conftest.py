from __future__ import annotations

import contextlib
import difflib
import hashlib
import os
import pathlib
import random
import string
from collections.abc import Callable
from typing import Protocol
from xml.dom import minidom
from xml.etree import ElementTree

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


@contextlib.contextmanager
def set_current_directory(path: pathlib.Path):
    origin = path.absolute()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(origin)


@pytest.fixture(scope="session")
def config_file_factory(tmpdir_factory):
    def _make_config_file(text: str) -> str:
        path = os.path.join(tmpdir_factory.mktemp("config_file"), "config.toml")
        with open(path, "w") as fp:
            fp.write(text)
        return path

    return _make_config_file


class LineCollectionMaker(Protocol):
    def __call__(
        self, line_count: int | None = ..., with_metadata: bool = ...
    ) -> vp.LineCollection: ...


@pytest.fixture
def make_line_collection() -> LineCollectionMaker:
    def _make_line_collection(
        line_count: int | None = None, with_metadata: bool = True
    ) -> vp.LineCollection:
        if line_count is None:
            line_count = random.randint(1, 10)
        if with_metadata:
            metadata = {
                vp.METADATA_FIELD_COLOR: vp.Color(
                    random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
                ),
                vp.METADATA_FIELD_NAME: "".join(
                    random.choice(string.ascii_letters) for _ in range(10)
                ),
                vp.METADATA_FIELD_PEN_WIDTH: vp.convert_length(f"{random.random()}mm"),
            }
        else:
            metadata = {}

        lc = vp.LineCollection(metadata=metadata)
        for _ in range(line_count):
            lc.append(
                [
                    random.random() * 100 + random.random() * 100j
                    for _ in range(random.randint(2, 10))
                ]
            )
        return lc

    return _make_line_collection


class DocumentMaker(Protocol):
    def __call__(self, layer_count: int = ...) -> vp.Document: ...


@pytest.fixture
def make_document(make_line_collection) -> DocumentMaker:
    def _make_document(layer_count: int = 1) -> vp.Document:
        doc = vp.Document()
        doc.page_size = 1000.0 * random.random(), 1000.0 * random.random()
        for _ in range(layer_count):
            doc.add(make_line_collection(), with_metadata=True)
        return doc

    return _make_document


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

    parser.addoption(
        "--store-ref-svg",
        action="store_true",
        help="Write reference SVGs for reference_svg().",
    )


def write_image_similarity_fail_report(
    image: Image.Image,
    reference_image: Image.Image,
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

    def _assert_image_similarity(img: Image.Image) -> None:
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
                if normalized_sum_sq_diff > 6.5:  # pragma: no cover
                    write_image_similarity_fail_report(
                        img, ref_img, img_arr, ref_img_arr, test_id, normalized_sum_sq_diff
                    )
                    pytest.fail(
                        f"image similarity test failed (rms: {normalized_sum_sq_diff})"
                    )

    return _assert_image_similarity


def _read_svg_lines(path: pathlib.Path) -> list[str]:
    tree = ElementTree.parse(path)
    xml_str = ElementTree.tostring(tree.getroot())
    # ET.canonicalize doesn't exist on Python 3.7
    canon = ElementTree.canonicalize(xml_str, strip_text=True)  # type: ignore
    lines = minidom.parseString(canon).toprettyxml().splitlines()
    return [line for line in lines if "<dc:source" not in line and "<dc:date" not in line]


def _write_reference_svg_fail_report(
    ref_lines: list[str],
    test_lines: list[str],
    test_id: str,
) -> None:
    report_dir = pathlib.Path(__file__).parent.parent / "test_report_reference_svg" / test_id
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "reference.svg").write_text("\n".join(ref_lines))
    (report_dir / "test.svg").write_text("\n".join(test_lines))


@pytest.fixture
def reference_svg(request, tmp_path) -> Callable:
    """Compare an SVG output to a saved reference.

    Use `--store-ref-svg` to save reference SVGs.

    Example::

        def test_ref_svg(reference_svg):
            with reference_svg() as path:
                export_svg_to(path)
    """

    store_ref_svg = request.config.getoption("--store-ref-svg")
    test_id = "refsvg_" + hashlib.md5(request.node.name.encode()).hexdigest() + ".svg"
    ref_path = pathlib.Path(REFERENCE_IMAGES_DIR) / test_id
    temp_file = tmp_path / test_id

    @contextlib.contextmanager
    def _reference_svg():
        nonlocal ref_path, temp_file, store_ref_svg

        yield temp_file

        if store_ref_svg:  # pragma: no cover
            ref_path.write_bytes(temp_file.read_bytes())
        else:
            if not ref_path.exists():  # pragma: no cover
                pytest.fail("reference SVG does not exist")

            temp_lines = _read_svg_lines(temp_file)
            ref_lines = _read_svg_lines(ref_path)

            if len(temp_lines) != len(ref_lines) or not all(
                a == b for a, b in zip(temp_lines, ref_lines)
            ):
                delta = difflib.unified_diff(
                    temp_lines,
                    ref_lines,
                    fromfile="<test result>",
                    tofile=str(ref_path.relative_to(pathlib.Path(REFERENCE_IMAGES_DIR))),
                    lineterm="",
                )

                _write_reference_svg_fail_report(ref_lines, temp_lines, request.node.name)

                pytest.fail("generated SVG does not match reference:\n" + "\n".join(delta))

    return _reference_svg
