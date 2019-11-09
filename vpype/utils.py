import click

UNITS = [
    ("px", 1.0),
    ("in", 96.0),
    ("mm", 96.0 / 25.4),
    ("cm", 96.0 / 2.54),
    ("pc", 16.0),
    ("pt", 96.0 / 72.0),
]


class Length(click.ParamType):
    name = "length"

    def convert(self, value, param, ctx):
        try:
            if isinstance(value, str):
                value = value.strip().lower()
                for unit, factor in UNITS:
                    if value.endswith(unit):
                        return float(value.strip(unit)) * factor

            return float(value)
        except ValueError:
            self.fail(f"parameter {value} is an incorrect length")
