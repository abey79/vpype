import vpype as vp

from . import render_image

doc = vp.read_multilayer_svg("/Users/hhip/src/vsketch/mywork/bezier_column_saved.svg", 0.1)
img = render_image(doc, (2048, 2048))
img.show()
