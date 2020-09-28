def test_config_is_empty(config_manager):
    assert config_manager.config == {}


def test_config_simple(config_manager, config_file_factory):
    path = config_file_factory(
        """
        a = 1
        b = true
        c = "hello"
        """
    )
    config_manager.load_config_file(path)
    assert config_manager.config == {"a": 1, "b": True, "c": "hello"}


def test_config_merge_dict_simple(config_manager, config_file_factory):
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

    config_manager.load_config_file(p1)
    config_manager.load_config_file(p2)
    assert config_manager.config == {"global": {"a": 1, "b": 2, "c": 3}}


def test_config_merge_dict_override(config_manager, config_file_factory):
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

    config_manager.load_config_file(p1)
    config_manager.load_config_file(p2)
    assert config_manager.config == {"global": {"a": 5, "b": 2, "c": 3}}


def test_config_merge_simple_array_must_overwrite(config_manager, config_file_factory):
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

    config_manager.load_config_file(p1)
    config_manager.load_config_file(p2)
    assert config_manager.config == {"a": 1, "b": [10, 11, 12], "c": 10}


def test_config_merge_table_must_extend(config_manager, config_file_factory):
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

    config_manager.load_config_file(p1)
    config_manager.load_config_file(p2)
    assert config_manager.config == {"test": [{"a": 1}, {"b": 2}]}
