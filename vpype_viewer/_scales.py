import enum
from dataclasses import dataclass
from typing import Tuple

MM_TO_PIXELS = 96.0 / 25.4
FT_TO_PIXELS = 12 * 96.0
IN_TO_PIXELS = 96.0


class UnitType(enum.Enum):
    """Type of unit to use for display purposes."""

    METRIC = enum.auto()
    IMPERIAL = enum.auto()
    PIXELS = enum.auto()


@dataclass
class ScaleSpec:
    scale: int  # in display unit
    divisions: Tuple[int, int, int]  # total sub-division, mid tick, small tick
    to_px: float  # conversion to px
    unit: str  # unit to display

    @property
    def scale_px(self) -> float:
        return self.scale * self.to_px


DEFAULT_SCALE_SPEC = ScaleSpec(1, (10, 5, 1), 1.0, "px")

# scale, division, mid, minor
PIXEL_SCALES = (
    ScaleSpec(5000, (10, 2, 1), 1.0, "px"),
    ScaleSpec(2000, (10, 5, 1), 1.0, "px"),
    ScaleSpec(1000, (10, 5, 1), 1.0, "px"),
    ScaleSpec(500, (10, 2, 1), 1.0, "px"),
    ScaleSpec(200, (10, 5, 1), 1.0, "px"),
    ScaleSpec(100, (10, 5, 1), 1.0, "px"),
    ScaleSpec(50, (10, 2, 1), 1.0, "px"),
    ScaleSpec(20, (10, 5, 1), 1.0, "px"),
    ScaleSpec(10, (10, 5, 1), 1.0, "px"),
    ScaleSpec(5, (10, 2, 1), 1.0, "px"),
    ScaleSpec(2, (10, 5, 1), 1.0, "px"),
    ScaleSpec(1, (10, 5, 1), 1.0, "px"),
)

METRIC_SCALES = (
    ScaleSpec(10, (10, 5, 1), 1000 * MM_TO_PIXELS, "m"),
    ScaleSpec(5, (10, 2, 1), 1000 * MM_TO_PIXELS, "m"),
    ScaleSpec(2, (10, 5, 1), 1000 * MM_TO_PIXELS, "m"),
    ScaleSpec(1, (10, 5, 1), 1000 * MM_TO_PIXELS, "m"),
    ScaleSpec(50, (10, 2, 1), 10 * MM_TO_PIXELS, "cm"),
    ScaleSpec(20, (10, 5, 1), 10 * MM_TO_PIXELS, "cm"),
    ScaleSpec(10, (10, 5, 1), 10 * MM_TO_PIXELS, "cm"),
    ScaleSpec(5, (10, 2, 1), 10 * MM_TO_PIXELS, "cm"),
    ScaleSpec(2, (10, 5, 1), 10 * MM_TO_PIXELS, "cm"),
    ScaleSpec(1, (10, 5, 1), 10 * MM_TO_PIXELS, "cm"),
    ScaleSpec(5, (10, 2, 1), MM_TO_PIXELS, "mm"),
    ScaleSpec(2, (10, 5, 1), MM_TO_PIXELS, "mm"),
    ScaleSpec(1, (10, 5, 1), MM_TO_PIXELS, "mm"),
)

IMPERIAL_SCALES = (
    ScaleSpec(100, (10, 5, 1), IN_TO_PIXELS, "in"),
    ScaleSpec(50, (10, 2, 1), IN_TO_PIXELS, "in"),
    ScaleSpec(20, (10, 5, 1), IN_TO_PIXELS, "in"),
    ScaleSpec(10, (10, 5, 1), IN_TO_PIXELS, "in"),
    ScaleSpec(5, (10, 2, 1), IN_TO_PIXELS, "in"),
    ScaleSpec(2, (16, 8, 4), IN_TO_PIXELS, "in"),
    ScaleSpec(1, (16, 8, 4), IN_TO_PIXELS, "in"),
)


SCALES_MAP = {
    UnitType.METRIC: METRIC_SCALES,
    UnitType.IMPERIAL: IMPERIAL_SCALES,
    UnitType.PIXELS: PIXEL_SCALES,
}
