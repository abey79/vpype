import click
import pytest

import vpype as vp
import vpype_cli


def test_float_type():
    @vpype_cli.cli.command(name="floatcmd")
    @click.argument("arg", type=vpype_cli.FloatType())
    @vpype_cli.generator
    def cmd(arg: float) -> vp.LineCollection:
        assert type(arg) is float
        return vp.LineCollection()

    vpype_cli.execute("floatcmd 3.5")
    with pytest.raises(click.BadParameter):
        vpype_cli.execute("floatcmd hello")


def test_int_range_type():
    @vpype_cli.cli.command(name="intrangecmd")
    @click.argument("arg", type=vpype_cli.IntRangeType(min=10, max=14))
    @vpype_cli.generator
    def cmd(arg: int) -> vp.LineCollection:
        assert type(arg) is int
        assert 10 <= arg <= 14
        return vp.LineCollection()

    vpype_cli.execute("intrangecmd 10")
    vpype_cli.execute("intrangecmd 14")
    with pytest.raises(click.BadParameter):
        vpype_cli.execute("intrangecmd 12.5")
    with pytest.raises(click.BadParameter):
        vpype_cli.execute("intrangecmd 9")


def test_choice_type():
    @vpype_cli.cli.command(name="choicecmd")
    @click.argument("arg", type=vpype_cli.ChoiceType(choices=["yes", "no"]))
    @vpype_cli.generator
    def cmd(arg: str) -> vp.LineCollection:
        assert arg in ["yes", "no"]
        return vp.LineCollection()

    vpype_cli.execute("choicecmd yes")
    vpype_cli.execute("choicecmd no")
    with pytest.raises(click.BadParameter):
        vpype_cli.execute("choicecmd maybe")
