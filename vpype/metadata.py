import dataclasses
from typing import Optional, Tuple, Union

import svgelements


@dataclasses.dataclass(frozen=True)
class Color:
    """Simple, immutable, hashable color class with flexible construction.

    Examples:

        >>> Color()
        Color(red=0, green=0, blue=0, alpha=255)
        >>> Color(255, 0, 255)
        Color(red=255, green=0, blue=255, alpha=255)
        >>> Color(255, 0, 255, 128)
        Color(red=255, green=0, blue=255, alpha=128)
        >>> red = Color("red")
        >>> red
        Color(red=255, green=0, blue=0, alpha=255)
        >>> Color(red)
        Color(red=255, green=0, blue=0, alpha=255)
        >>> Color(svgelements.Color("#0f0"))
        Color(red=0, green=255, blue=0, alpha=255)
    """

    red: int
    green: int
    blue: int
    alpha: int

    def __init__(
        self,
        red: Optional[Union[int, str, "Color", svgelements.Color]] = None,
        green: Optional[int] = None,
        blue: Optional[int] = None,
        alpha: Optional[int] = None,
    ):
        svgc = None
        if isinstance(red, (svgelements.Color, Color)):
            svgc = red
        elif isinstance(red, str):
            svgc = svgelements.Color(red)
        if svgc is not None:
            red, green, blue, alpha = svgc.red, svgc.green, svgc.blue, svgc.alpha

        object.__setattr__(self, "red", int(red or 0))
        object.__setattr__(self, "green", int(green or 0))
        object.__setattr__(self, "blue", int(blue or 0))
        object.__setattr__(self, "alpha", int(alpha or 255))

    def as_floats(self) -> Tuple[float, float, float, float]:
        return self.red / 255, self.green / 255, self.blue / 255, self.alpha / 255


METADATA_SYSTEM_FIELD_TYPES = {
    "vp:name": str,
    "vp:color": Color,
    "vp:pen_width": float,
}

# noinspection HttpUrlsUsage
METADATA_SVG_NAMESPACES = {
    "http://www.inkscape.org/namespaces/inkscape": "inkscape",
    "http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd": "sodipodi",
    "http://purl.org/dc/elements/1.1/": "dc",
    "http://creativecommons.org/ns": "cc",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns": "rdf",
}
