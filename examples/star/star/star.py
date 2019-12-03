import click
#from vpype import LineCollection, generator
from vpype.model import LineCollection
from vpype.decorators import generator
#from vpype.vpype import cli
#import vpype

@click.command()
#@cli.command(group="test")
@generator
def star():
    """
    Hello
    """
    lc = LineCollection()
    lc.append([0, 1+1j, 3+2j, 0+1j, 0])
    return lc

