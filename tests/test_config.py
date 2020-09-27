import pytest

import vpype as vp


@pytest.fixture
def cfg():
    return vp.ConfigManager()


def test_config_is_empty(cfg):
    assert cfg.config == {}


def test_config_simple(cfg, tmp_path):
    path = tmp_path / "config.toml"
    path.write_text(
        """
        a = 1
        b = true
        c = "hello"
        """
    )
    cfg.load_config_file(str(path))
    assert cfg.config == {"a": 1, "b": True, "c": "hello"}


def test_config_merge_dict_simple(cfg, tmp_path):
    p1 = tmp_path / "config1.toml"
    p2 = tmp_path / "config2.toml"
    p1.write_text(
        """
        [global]
        a = 1
        b = 2
        """
    )
    p2.write_text(
        """
        [global]
        c = 3
        """
    )

    cfg.load_config_file(str(p1))
    cfg.load_config_file(str(p2))
    assert cfg.config == {"global": {"a": 1, "b": 2, "c": 3}}


def test_config_merge_dict_override(cfg, tmp_path):
    p1 = tmp_path / "config1.toml"
    p2 = tmp_path / "config2.toml"
    p1.write_text(
        """
        [global]
        a = 1
        b = 2
        """
    )
    p2.write_text(
        """
        [global]
        a = 5
        c = 3
        """
    )

    cfg.load_config_file(str(p1))
    cfg.load_config_file(str(p2))
    assert cfg.config == {"global": {"a": 5, "b": 2, "c": 3}}


def test_config_merge_simple_array_must_overwrite(cfg, tmp_path):
    p1 = tmp_path / "config1.toml"
    p2 = tmp_path / "config2.toml"
    p1.write_text(
        """
        a = 1
        b = [5, 6, 7]
        """
    )
    p2.write_text(
        """
        c = 10
        b = [10, 11, 12]
        """
    )

    cfg.load_config_file(str(p1))
    cfg.load_config_file(str(p2))
    assert cfg.config == {"a": 1, "b": [10, 11, 12], "c": 10}


def test_config_merge_table_must_extend(cfg, tmp_path):
    p1 = tmp_path / "config1.toml"
    p2 = tmp_path / "config2.toml"
    p1.write_text(
        """
        [[test]]
        a = 1
        """
    )
    p2.write_text(
        """
        [[test]]
        b = 2
        """
    )

    cfg.load_config_file(str(p1))
    cfg.load_config_file(str(p2))
    assert cfg.config == {"test": [{"a": 1}, {"b": 2}]}
