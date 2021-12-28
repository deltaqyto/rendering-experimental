import math
from objects import Object, RectObject, RegPoly, Circle, ShadedRect, FractalRenderer


def printreturn(value):  # Handy function for the print lambda
    print(value)
    return value


def get_maps():
    # /Parse map binds:
    # const:: returns whatever constant value is provided to it
    # const_group:: uses a lookup value to look through a set of matches, picking the one with the closest key that is smaller than it,
    # then returning the matching value
    # fsine:: takes the frame, multiplies it by a constant, then sines and multiplies it again by another constant
    # aspect:: returns the aspect ratio of the display
    # frame:: returns the frame count
    # extra:: generic
    # /End

    # /Mix map binds:
    # alpha:: transparency to be multiplied
    # extra:: generic
    # /End

    parse_map = {"const": [0, 1, lambda v, c, e, s: c[0]], "multiply": [1, 1, lambda v, c, e, s: c[0] * v[0]],
                 "frame": [0, 0, lambda v, c, e, s: e["frames"]], "add": [1, 1, lambda v, c, e, s: c[0] + v[0]],
                 "sine": [1, 0, lambda v, c, e, s: math.sin(v[0])], "floor": [1, 1, lambda v, c, e, s: c[0] * math.floor(v[0] / c[0])],
                 "lookup": [0, 3, lambda v, c, e, s: s.get(c[0], {}).get(c[1]) if s.get(c[0]).get(c[1]) is not None else c[2]],
                 "fsine": [0, 2, lambda v, c, e, s: c[1] * math.sin(c[0] * e["frames"])], "abs": [1, 0, lambda v, c, e, s: math.fabs(v[0])],
                 "print": [1, 0, lambda v, c, e, s: printreturn(v[0])], "const_group": [1, 3, lambda v, c, e, s: const_group(v[0], c[0], c[1], c[2])],
                 "aspect": [0, 0, lambda v, c, e, s: e["aspect"]]}
    "/End"

    mix_map = {"alpha": "mult", "pos_x": "add", "pos_y": "add", "visible": "inherit", "unused": "ignore", "size_x": "mult", "size_y": "mult",
               "faces": "add", "clip_rect": "passthrough"}  # Should "inherit" by default
    "/End"
    object_map = {"rect": RectObject, "regpoly": RegPoly, "circle": Circle, "shadrect": ShadedRect, "fractalrect": FractalRenderer}
    "/End"

    return {"parse": parse_map, "mix": mix_map, "objects": object_map}


def const_group(driver, values, timings, default):
    valid = None
    for time, val in zip(timings, values):
        if driver >= time:
            valid = val
        else:
            return default if valid is None else valid
    return default if valid is None else valid
