from __future__ import annotations

import logging

from .config import config_manager

# deprecated
CONFIG_MANAGER = config_manager


def block_processor(*args, **kwargs):  # pragma: no cover
    import vpype_cli

    logging.warning(
        "!!! `@vpype.block_processor` is deprecated, "
        "use `@vpype_cli.block_processor` instead."
    )
    return vpype_cli.block_processor(*args, **kwargs)


def generator(*args, **kwargs):  # pragma: no cover
    import vpype_cli

    logging.warning(
        "!!! `@vpype.generator` is deprecated, use `@vpype_cli.generator` instead."
    )
    return vpype_cli.generator(*args, **kwargs)


def global_processor(*args, **kwargs):  # pragma: no cover
    import vpype_cli

    logging.warning(
        "!!! `@vpype.global_processor` is deprecated, "
        "use `@vpype_cli.global_processor` instead."
    )
    return vpype_cli.global_processor(*args, **kwargs)


def layer_processor(*args, **kwargs):  # pragma: no cover
    import vpype_cli

    logging.warning(
        "!!! `@vpype.layer_processor` is deprecated, use `@vpype_cli.layer_processor` instead."
    )
    return vpype_cli.layer_processor(*args, **kwargs)


def pass_state(*args, **kwargs):  # pragma: no cover
    import vpype_cli

    logging.warning(
        "!!! `@vpype.pass_state` is deprecated, use `@vpype_cli.pass_state` instead."
    )
    return vpype_cli.pass_state(*args, **kwargs)


class AngleType:  # pragma: no cover
    def __new__(cls):
        import vpype_cli

        logging.warning(
            "!!! `vpype.AngleType` is deprecated, use `vpype_cli.AngleType` instead."
        )
        return vpype_cli.AngleType()


class LayerType:  # pragma: no cover
    def __new__(cls, *args, **kwargs):
        import vpype_cli

        logging.warning(
            "!!! `vpype.LayerType` is deprecated, use `vpype_cli.LayerType` instead."
        )
        return vpype_cli.LayerType(*args, **kwargs)


class LengthType:  # pragma: no cover
    def __new__(cls):
        import vpype_cli

        logging.warning(
            "!!! `vpype.LengthType` is deprecated, use `vpype_cli.LengthType` instead."
        )
        return vpype_cli.LengthType()


class PageSizeType:  # pragma: no cover
    def __new__(cls):
        import vpype_cli

        logging.warning(
            "!!! `vpype.PageSizeType` is deprecated, use `vpype_cli.PageSizeType` instead."
        )
        return vpype_cli.PageSizeType()


def multiple_to_layer_ids(*args, **kwargs):  # pragma: no cover
    import vpype_cli

    logging.warning(
        "!!! `vpype.multiple_to_layer_ids` is deprecated, "
        "use `vpype_cli.multiple_to_layer_ids` instead."
    )
    return vpype_cli.multiple_to_layer_ids(*args, **kwargs)


def single_to_layer_id(*args, **kwargs):  # pragma: no cover
    import vpype_cli

    logging.warning(
        "!!! `vpype.single_to_layer_id` is deprecated, "
        "use `vpype_cli.single_to_layer_id` instead."
    )
    return vpype_cli.single_to_layer_id(*args, **kwargs)
