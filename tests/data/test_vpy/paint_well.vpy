# inspired by use-case described in https://github.com/abey79/vpype/issues/501

read paint_well_svgs/multilayer.svg
forlayer
  lmove %_lid% 1
  splitdist 1m
  forlayer
    lmove %_lid% %_lid*2%
    read -l %_lid*2-1% paint_well_svgs/well_%_name%.svg
  end
  lmove all %_lid%

  # restore name and color for layer
  name -l %_lid% %_name%
  color -l %_lid% %_color%
end