import math


def parse_attribute_functions(attribs, eval_vals, shared_data):
    def printreturn(value):  # Handy function for the print lambda
        print(value)
        return value

    if not attribs:
        return {}
    new_attribs = {}

    # Lambda takes 4 inputs. A list of stack values, a list of provided constants, the dict of evaluators and the dict of shared data
    method_lookup = {"const": [0, 1, lambda v, c, e, s: c[0]], "multiply": [1, 1, lambda v, c, e, s: c[0] * v[0]],
                     "frame": [0, 0, lambda v, c, e, s: e["frames"]], "add": [1, 1, lambda v, c, e, s: c[0] + v[0]],
                     "sine": [1, 0, lambda v, c, e, s: math.sin(v[0])], "floor": [1, 1, lambda v, c, e, s: c[0] * math.floor(v[0] / c[0])],
                     "lookup": [0, 3, lambda v, c, e, s: s.get(c[0], {}).get(c[1]) if s.get(c[0]).get(c[1]) is not None else c[2]],
                     "fsine": [0, 2, lambda v, c, e, s: c[1] * math.sin(c[0] * e["frames"])], "abs": [1, 0, lambda v, c, e, s: math.fabs(v[0])],
                     "print": [1, 0, lambda v, c, e, s: printreturn(v[0])]}

    for name, attr in attribs.items():
        # Handle trivial case where no command group is provided
        if not isinstance(attr, (list, tuple)):
            new_attribs[name] = attr
            continue
        # Handle case where only one command is provided
        if not isinstance(attr[0], (list, tuple)):
            new_attribs[name] = method_lookup[attr[0]][2]([], attr[1:], eval_vals, shared_data)
            continue

        # Check for vector count
        try:
            count = int(attr[0][0])
            instructions = attr[0][1:]
        except ValueError:
            count = 1
            instructions = attr[0]

        output = []
        values = []
        constants = attr[1:] if len(attr) > 1 else []
        for index in range(count):
            for instruction in instructions:
                method = method_lookup[instruction]
                pass_consts = constants[:method[1]]
                constants = constants[method[1]:]
                pass_vals = [values.pop() for _ in range(method[0])]
                outval = method[2](pass_vals, pass_consts, eval_vals, shared_data)
                if not isinstance(outval, (list, tuple)):
                    values.append(outval)
                elif len(outval) != count:
                    values.append(outval)
                else:
                    values.append(outval[index])
            output.append(values[-1])

        # Save output
        if count == 1:
            new_attribs[name] = output[0]
        else:
            new_attribs[name] = output

    return new_attribs


def mix_attributes(attrib_set_1, attrib_set_2, default_attrs):
    """Each name in default_attrs is returned with a value derived from attrib sets 1 and 2.
    Mix behaviors allows selection of the mix type for different names"""
    mix_behaviours = {"alpha": "mult", "pos_x": "add", "pos_y": "add", "visible": "inherit", "unused": "ignore"}  # Should "inherit" by default
    out_attrs = {}
    for name, attr in default_attrs.items():
        mode = mix_behaviours.get(name, "inherit")
        if mode == "mult":
            out_attrs[name] = attrib_set_1.get(name, 1) * attrib_set_2.get(name, 1) if name in attrib_set_1 or name in attrib_set_2 else attr[0]
        elif mode == "add":
            out_attrs[name] = attrib_set_1.get(name, 0) + attrib_set_2.get(name, 0) if name in attrib_set_1 or name in attrib_set_2 else attr[0]

        elif mode == "inherit":
            out_attrs[name] = attr[0] if name not in attrib_set_1 else attrib_set_1[name]

    return out_attrs