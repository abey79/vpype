#!/bin/bash

# Grid of alien letters.
# Note how the grid size are argument to the `grid` command, and must thus be passed
# after the options such as `--offset`. This is the same for the `write` command, where
# the output file path is the argument.

vpype begin grid --offset 1.5cm 1.5cm 13 20 \
  script alien_letter.py \
  scale --to 0.8cm 0.8cm \
end \
write --page-format a3 --center alien.svg