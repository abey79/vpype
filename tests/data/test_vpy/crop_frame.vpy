read two_layers_a4.svg
eval "m = 3*cm; w, h = prop.vp_page_size"
crop %m% %m% "%w-2*m%" "%h-2*m%"
rect %m% %m% "%w-2*m%" "%h-2*m%"