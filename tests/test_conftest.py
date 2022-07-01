import vpype as vp


def test_make_line_collection(make_line_collection):
    lc = make_line_collection(with_metadata=False)
    assert lc.metadata == {}
    assert len(lc) > 0

    lc = make_line_collection(with_metadata=True)
    assert vp.METADATA_FIELD_NAME in lc.metadata
    assert isinstance(lc.metadata[vp.METADATA_FIELD_COLOR], vp.Color)
    assert isinstance(lc.metadata[vp.METADATA_FIELD_PEN_WIDTH], float)
    assert len(lc) > 0


def test_make_document(make_document):
    doc = make_document(layer_count=3)
    assert len(doc.layers) == 3
    assert doc.page_size is not None
    for lc in doc.layers.values():
        assert vp.METADATA_FIELD_NAME in lc.metadata
        assert isinstance(lc.metadata[vp.METADATA_FIELD_COLOR], vp.Color)
        assert isinstance(lc.metadata[vp.METADATA_FIELD_PEN_WIDTH], float)
        assert len(lc) > 0
