import math
from objects import Object, RectObject, RegPoly, Circle, ShadedRect, FractalRenderer


def printreturn(value):  # Handy function for the print lambda
    print(value)
    return value


def const_group(driver, values, timings, default):
    valid = None
    for time, val in zip(timings, values):
        if driver >= time:
            valid = val
        else:
            return valid
    if valid is not None:
        return valid
    return default


def get_maps():
    parse_map = {"const": [0, 1, lambda v, c, e, s: c[0]], "multiply": [1, 1, lambda v, c, e, s: c[0] * v[0]],
                 "frame": [0, 0, lambda v, c, e, s: e["frames"]], "add": [1, 1, lambda v, c, e, s: c[0] + v[0]],
                 "sine": [1, 0, lambda v, c, e, s: math.sin(v[0])], "floor": [1, 1, lambda v, c, e, s: c[0] * math.floor(v[0] / c[0])],
                 "lookup": [0, 3, lambda v, c, e, s: s.get(c[0], {}).get(c[1]) if s.get(c[0]).get(c[1]) is not None else c[2]],
                 "fsine": [0, 2, lambda v, c, e, s: c[1] * math.sin(c[0] * e["frames"])], "abs": [1, 0, lambda v, c, e, s: math.fabs(v[0])],
                 "print": [1, 0, lambda v, c, e, s: printreturn(v[0])], "const_group": [1, 3, lambda v, c, e, s: const_group(v[0], c[0], c[1], c[2])],
                 "aspect": [0, 0, lambda v, c, e, s: e["aspect"]], "inv_aspect": [0, 0, lambda v, c, e, s: 1 / e["aspect"]]}

    mix_map = {"alpha": "mult", "pos_x": "add", "pos_y": "add", "visible": "inherit", "unused": "ignore", "size_x": "mult", "size_y": "mult",
               "faces": "add", "clip_rect": "passthrough"}  # Should "inherit" by default
    object_map = {"rect": RectObject, "regpoly": RegPoly, "circle": Circle, "shadrect": ShadedRect, "fractalrect": FractalRenderer}

    return {"parse": parse_map, "mix": mix_map, "objects": object_map}
