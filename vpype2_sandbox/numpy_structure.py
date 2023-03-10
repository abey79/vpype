import numpy as np

LineType = np.dtype([("start", complex), ("end", complex), ("pts", 1)])
polyline = np.array([(3, 5), (6, 7)], dtype=LineType)
print(polyline)
