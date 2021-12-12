import math


def parse_attribute_functions(attribs, eval_vals, shared_data, method_lookup):
    def printreturn(value):  # Handy function for the print lambda
        print(value)
        return value

    if not attribs:
        return {}
    new_attribs = {}

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


def mix_attributes(attrib_set_1, attrib_set_2, default_attrs, mix_behaviours):
    """Each name in default_attrs is returned with a value derived from attrib sets 1 and 2.
    Mix behaviors allows selection of the mix type for different names"""
    out_attrs = {}
    for name, attr in default_attrs.items():
        mode = mix_behaviours.get(name, "inherit")
        if mode == "mult":
            out_attrs[name] = attrib_set_1.get(name, 1) * attrib_set_2.get(name, 1) if name in attrib_set_1 or name in attrib_set_2 else attr[0]
        elif mode == "add":
            out_attrs[name] = attrib_set_1.get(name, 0) + attrib_set_2.get(name, 0) if name in attrib_set_1 or name in attrib_set_2 else attr[0]

        elif mode == "inherit":
            out_attrs[name] = attr[0] if name not in attrib_set_1 else attrib_set_1[name]
        elif mode == "ignore":
            out_attrs[name] = attr[0] if name not in attrib_set_2 else attrib_set_2[name]

    return out_attrs