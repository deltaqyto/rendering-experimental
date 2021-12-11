import math
from objects import Object, RectObject, RegPoly, Circle


def printreturn(value):  # Handy function for the print lambda
    print(value)
    return value


def get_maps():
    parse_map = {"const": [0, 1, lambda v, c, e, s: c[0]], "multiply": [1, 1, lambda v, c, e, s: c[0] * v[0]],
                         "frame": [0, 0, lambda v, c, e, s: e["frames"]], "add": [1, 1, lambda v, c, e, s: c[0] + v[0]],
                         "sine": [1, 0, lambda v, c, e, s: math.sin(v[0])], "floor": [1, 1, lambda v, c, e, s: c[0] * math.floor(v[0] / c[0])],
                         "lookup": [0, 3, lambda v, c, e, s: s.get(c[0], {}).get(c[1]) if s.get(c[0]).get(c[1]) is not None else c[2]],
                         "fsine": [0, 2, lambda v, c, e, s: c[1] * math.sin(c[0] * e["frames"])], "abs": [1, 0, lambda v, c, e, s: math.fabs(v[0])],
                         "print": [1, 0, lambda v, c, e, s: printreturn(v[0])]}

    mix_map = {"alpha": "mult", "pos_x": "add", "pos_y": "add", "visible": "inherit", "unused": "ignore"}  # Should "inherit" by default
    object_map = {"rect": RectObject, "regpoly": RegPoly, "circle": Circle}

    return {"parse": parse_map, "mix": mix_map, "objects": object_map}
