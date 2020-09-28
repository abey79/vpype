import pytest

import vpype as vp


@pytest.fixture
def cfg():
    return vp.ConfigManager()


@pytest.fixture
def config_file_factory(tmp_path_factory):
    def _make_config_file(text: str) -> str:
        path = tmp_path_factory.mktemp("config_file") / "config.toml"
        path.write_text(text)
        return str(path)

    return _make_config_file


def test_config_is_empty(cfg):
    assert cfg.config == {}


def test_config_simple(cfg, config_file_factory):
    path = config_file_factory(
        """
        a = 1
        b = true
        c = "hello"
        """
    )
    cfg.load_config_file(path)
    assert cfg.config == {"a": 1, "b": True, "c": "hello"}


def test_config_merge_dict_simple(cfg, config_file_factory):
    p1 = config_file_factory(
        """
        [global]
        a = 1
        b = 2
        """
    )
    p2 = config_file_factory(
        """
        [global]
        c = 3
        """
    )

    cfg.load_config_file(p1)
    cfg.load_config_file(p2)
    assert cfg.config == {"global": {"a": 1, "b": 2, "c": 3}}


def test_config_merge_dict_override(cfg, config_file_factory):
    p1 = config_file_factory(
        """
        [global]
        a = 1
        b = 2
        """
    )
    p2 = config_file_factory(
        """
        [global]
        a = 5
        c = 3
        """
    )

    cfg.load_config_file(p1)
    cfg.load_config_file(p2)
    assert cfg.config == {"global": {"a": 5, "b": 2, "c": 3}}


def test_config_merge_simple_array_must_overwrite(cfg, config_file_factory):
    p1 = config_file_factory(
        """
        a = 1
        b = [5, 6, 7]
        """
    )
    p2 = config_file_factory(
        """
        c = 10
        b = [10, 11, 12]
        """
    )

    cfg.load_config_file(p1)
    cfg.load_config_file(p2)
    assert cfg.config == {"a": 1, "b": [10, 11, 12], "c": 10}


def test_config_merge_table_must_extend(cfg, config_file_factory):
    p1 = config_file_factory(
        """
        [[test]]
        a = 1
        """
    )
    p2 = config_file_factory(
        """
        [[test]]
        b = 2
        """
    )

    cfg.load_config_file(p1)
    cfg.load_config_file(p2)
    assert cfg.config == {"test": [{"a": 1}, {"b": 2}]}
