import copy

import pytest

import vpype as vp
import vpype_cli

from .test_commands import EXAMPLE_SVG_DIR

BLOCKS = [
    f"forfile '{EXAMPLE_SVG_DIR / '*.svg'}'",
    f"forlayer",
    f"grid -k 2 2",
    f"repeat 3",
]


@vpype_cli.cli.command()
@vpype_cli.global_processor
def doccopy(doc: vp.Document) -> vp.Document:
    """This command has no effect on the pipeline, but creates completely new copies of the
    pipeline's document and its content. This is useful to test the behaviour of blocks."""
    return copy.deepcopy(doc)


def test_doccopy(make_document):
    doc = make_document()
    new_doc = vpype_cli.execute("doccopy", document=doc)
    assert doc is not new_doc
    assert doc == new_doc


@pytest.mark.parametrize("block", BLOCKS)
def test_block_doccopy_same(block, make_document):
    doc = make_document()
    new_doc = vpype_cli.execute(f"{block} doccopy end", document=doc)
    assert doc == new_doc


@pytest.mark.parametrize("block", BLOCKS)
def test_block_doccopy_different(block, make_document):
    doc = make_document()
    new_doc = vpype_cli.execute(f"{block} doccopy line 0 0 10 10 end", document=doc)
    assert doc != new_doc


def test_forlayer_property_accessor():
    doc = vpype_cli.execute(
        "pens rgb forlayer eval '_prop.test=_i;_prop.test2=_prop.test' end"
    )
    for i in range(3):
        assert doc.layers[i + 1].property("test") == i
        assert doc.layers[i + 1].property("test2") == i

    doc = vpype_cli.execute(
        'pens rgb forlayer eval \'_prop["test"]=_i;_prop["test2"]=_prop["test"]\' end'
    )
    for i in range(3):
        assert doc.layers[i + 1].property("test") == i
        assert doc.layers[i + 1].property("test2") == i


def test_forlayer_vars():
    vpype_cli.execute(
        """
        repeat 5
            random -l new
        end 
        eval 'cnt=0'
        forlayer
            eval 'assert _lid==cnt+1'
            eval 'assert _i==cnt;cnt += 1'
            eval 'assert _n==5'
        end"""
    )


def test_forlayer_move_by_one(make_document):
    doc = make_document(layer_count=3)

    new_doc = vpype_cli.execute("forlayer lmove %_lid% %_lid+1% end", document=copy.copy(doc))
    assert len(new_doc.layers) == 3
    for lid, layer in doc.layers.items():
        assert layer == new_doc.layers[lid + 1]


def test_forlayer_merge_to_layer_one(make_line_collection):
    l1, l2 = make_line_collection(), make_line_collection()
    doc = vp.Document()
    doc.add(copy.copy(l1), with_metadata=True)
    doc.add(copy.copy(l2), with_metadata=True)

    new_doc = vpype_cli.execute("forlayer lmove %_lid% 1 end", document=copy.copy(doc))

    expected = vp.LineCollection(metadata=l2.metadata)
    expected.extend(l1)
    expected.extend(l2)

    assert new_doc.layers[1] == expected
    assert len(new_doc.layers) == 1
    assert new_doc.page_size == doc.page_size


def test_forlayer_delete(make_document):
    doc = make_document(layer_count=3)
    new_doc = vpype_cli.execute("forlayer ldelete %_lid% end", document=copy.copy(doc))

    assert len(new_doc.layers) == 0
    assert new_doc.page_size == doc.page_size
