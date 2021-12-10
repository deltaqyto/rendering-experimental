import math
import yaml
import bindings as gl


# Current priorities, in order:
# Todo enable scene rendering + proper attribute handling


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


class Object:
    def __init__(self, name, attributes):
        self.name = name
        self.vao = gl.Vao()
        self.vbo = gl.Vbo()
        self.type = "Undef"
        self.attributes = attributes
        self.default_attrs = {}

    def __del__(self):
        self.vao.free()
        self.vbo.free()

    def render(self, evaluators, shared_data, external_attrs):
        evaluated_attrs = parse_attribute_functions(self.attributes, evaluators, shared_data)
        mixed_attrs = mix_attributes(evaluated_attrs, external_attrs, self.default_attrs)
        self.draw({**mixed_attrs, **shared_data})

    def draw(self, draw_attrs):
        raise NotImplementedError()

    def __repr__(self):
        return f"{self.type} object {self.name}"

    def list_attributes(self):
        print(f"{self.type} object: {self.name}")
        for name, attr in self.attributes.items():
            print(f"{name}, assume {attr[0]}, {attr[1]}")
        print()


class RectObject(Object):
    def __init__(self, name, attributes):
        super().__init__(name, attributes)
        self.vao.set_row_size(2)
        self.vao.assign_data(0, 2)
        self.vao.enable()
        self.vertices = [-1.0, -1.0, 1.0, 1.0, -1.0, 1.0,
                         -1.0, -1.0, 1.0, -1.0, 1.0, 1.0]
        self.vbo.add_data(self.vertices, gl.GL_const.static_draw)
        self.vao.add_vbo(self.vbo)

        self.default_attrs = {"size_x": [0.5, "horizontal scale factor"], "size_y": [0.5, "vertical scale factor"],
                              "pos_x": [0, "offset from center along x"], "pos_y": [0, "offset from center along y"],
                              "color": [(1, 0, 1), "primary color of shape"]}
        self.type = "Rectangle"

    def draw(self, draw_attrs):
        # todo add line_weight, radius
        matrix = gl.Mat4(1.0)
        matrix = gl.translate(matrix, gl.Vec3(draw_attrs.get("pos_x"), draw_attrs.get("pos_y"), 0))
        matrix = gl.scale(matrix, gl.Vec3(draw_attrs.get("size_x"), draw_attrs.get("size_y"), 1))
        self.vao.draw_mode(gl.Vao.Modes.fill)

        color = draw_attrs.get("color")

        draw_attrs.get("shader").setMat4("matrix", matrix)
        draw_attrs.get("shader").setVec3("color", *color)

        self.vao.draw_verts(0, 0, True)


class RegPoly(Object):
    def __init__(self, name, attributes):
        super().__init__(name, attributes)
        self.vao.set_row_size(2)
        self.vao.assign_data(0, 2)
        self.ebo = gl.Ebo()

        self.default_attrs = {"size_x": [0.5, "horizontal scale factor"], "size_y": [0.5, "vertical scale factor"],
                              "pos_x": [0, "offset from center along x"], "pos_y": [0, "offset from center along y"],
                              "color": [(1, 0, 1), "primary color of shape"], "faces": [4, "number of sides on polygon"],
                              "max_faces": [64, "largest number of faces the shape can have"]}

        self.vertices = [0 for _ in range(self.default_attrs["max_faces"][0] * 2 + 2)]
        self.indices = [0 for _ in range(self.default_attrs["max_faces"][0] * 3)]

        self.vbo.add_data(self.vertices, gl.GL_const.dynamic_draw)
        self.ebo.add_data(self.indices, gl.GL_const.dynamic_draw)

        self.vao.add_vbo(self.vbo)
        self.vao.add_ebo(self.ebo)

        self.type = "Regular Polygon"

    def distribute(self, a, b, num):
        """Get intersection point of a line y = mx and ellipse x^2/a^2 + y^2/b^2 = 1, for num points spaced with equal separation angles """
        out_points = []
        num = round(num)

        if a == 0 or b == 0 or num == 0:  # Catch division by zero and trivial cases
            return out_points

        divisor = 2 * math.pi / num
        for cur in range(num):
            m = divisor * cur

            if m == math.pi / 2:  # Catch cases where tan(m) would be infinite
                out_points += [0, b]
                continue
            if m == 3 * math.pi / 2:
                out_points += [0, -b]
                continue

            # Decide which side of the origin the intersection is
            multiplier = 1 if 0 <= m < math.pi / 2 or 3 * math.pi / 2 < m <= 2 * math.pi else -1

            m = math.tan(m)
            intersection = [((a * a * b * b) / (a * a * m * m + b * b)) ** 0.5 * multiplier, 0]
            intersection[1] = m * intersection[0]  # Get y coord of the intersect y = mx
            out_points += intersection
        return out_points

    def tri_fan_indices(self, num):
        """Generate indices list for a triangle fan with num faces"""
        output = []
        for count in range(round(num)):
            output += [0, count + 1, count + 2]
        if output:
            output[-1] = 1
        return output

    def __del__(self):
        self.ebo.free()
        super().__del__()

    def draw(self, draw_attrs):
        faces = max(3, min(draw_attrs.get("faces"), draw_attrs.get("max_faces")))
        self.vertices = [0, 0] + self.distribute(0.8, 0.8, faces)
        self.indices = self.tri_fan_indices(faces)

        self.vbo.add_data(self.vertices, gl.GL_const.dynamic_draw)
        self.ebo.add_data(self.indices, gl.GL_const.dynamic_draw)

        matrix = gl.Mat4(1.0)
        matrix = gl.translate(matrix, gl.Vec3(draw_attrs.get("pos_x"), draw_attrs.get("pos_y"), 0))
        matrix = gl.scale(matrix, gl.Vec3(draw_attrs.get("size_x") * draw_attrs.get("aspect"), draw_attrs.get("size_y"), 1))
        self.vao.draw_mode(gl.Vao.Modes.fill)

        draw_attrs.get("shader").setMat4("matrix", matrix)
        draw_attrs.get("shader").setVec3("color", *draw_attrs.get("color"))

        self.vao.draw_elements(0, 0, True)


class Circle(RegPoly):
    def __init__(self, name, attributes):
        super().__init__(name, attributes)
        self.default_attrs["faces"][0] = self.default_attrs["max_faces"][0]  # At faces > 20 looks like a circle enough


class Scene:
    def __init__(self, name, sc_children=None, obj_children=None, self_attrs=None):
        self.sc_children = sc_children if sc_children is not None else {}
        self.obj_children = obj_children if obj_children is not None else {}
        self.attributes = self_attrs if self_attrs is not None else {}
        self.name = name

        self.default_attrs = {"size_x": [0.5, "horizontal scale factor"], "size_y": [0.5, "vertical scale factor"],
                              "pos_x": [0, "offset from center along x"], "pos_y": [0, "offset from center along y"]}

    def add_scene(self, child):
        self.sc_children.append(child)

    def add_object(self, child):
        self.obj_children.append(child)

    def render(self, evaluators, objects, scenes, shared_data, depth, external_attrs=None):
        external_attrs = {} if external_attrs is None else external_attrs
        evaluated_attrs = parse_attribute_functions(self.attributes, evaluators, shared_data)
        mixed_attrs = mix_attributes(evaluated_attrs, external_attrs, self.default_attrs)
        self.draw(objects, scenes, {**mixed_attrs, **shared_data}, evaluators, shared_data, depth)

    def draw(self, objects, scenes, inheritables, evaluators, shared_data, depth):

        # Render all objects
        for name, obj_attrs in self.obj_children.items():
            if name not in objects:
                print("skip")
                continue
            objects[name].render(evaluators, shared_data, inheritables)

        # Render all scenes
        if depth < 0:
            return
        for name, scene_attrs in self.sc_children.items():
            if name not in scenes:
                continue
            scenes[name].render(evaluators, objects, scenes, shared_data, depth - 1, inheritables)  # Incomplete, needs parent attributes to be parsed and passed

    def __repr__(self):
        return f"Scene {self.name}"


class Project:
    def __init__(self, name):
        self.name = name
        self.scenes = {}
        self.objects = []
        self.attributes = {}
        self.setup = {}
        self.shared_data = {}
        self.object_types = {"rect": RectObject, "regpoly": RegPoly, "circle": Circle}

        self.background_color = [0, 0, 0]

    def update_object_types(self, types):
        self.object_types.update(types)

    def render(self, passthrough_attribs):
        self.attributes.update(passthrough_attribs)
        base_scene = self.scenes["root"].render(self.attributes, self.objects, self.scenes, {**self.shared_data, **self.attributes},
                                                self.setup.get("max_draw_depth", 5))
        return base_scene

    def load(self, file_name):
        """
        Load in all scenes and objects, assign relations to each node
        """
        self.scenes = {}
        self.objects = {}
        self.setup = {}
        with open(file_name) as file:
            data = yaml.load(file, Loader=yaml.FullLoader)

            # Handy contractions
            scenes = data["graph"]["scenes"]
            objects = data["graph"]["objects"]

            # Save to project memory
            self.shared_data = data["shared_data"]
            self.setup = data["setup"]

            # Process object and scene dictionaries
            self.objects = {name: self.object_types.get(obj["type"])(name, obj) for name, obj in objects.items()}
            self.scenes = {name: Scene(name, sc["scenes"], sc["objects"], sc["self"]) for name, sc in scenes.items()}

        self.background_color = self.shared_data.get("background", [0, 0, 0])


def main():
    scale = 1
    size_x = round(720 * scale)
    size_y = round(480 * scale)

    screen = gl.Screen(4, 6, size_x, size_y, "example")

    project = Project("base")
    project.load("debug.yaml")

    frame_rate = project.setup["frame_rate"]
    elapsed_frames = 0

    step_mode = "play"
    scrubbing_repeat_time = 0.1
    key_press_timers = [0, 0]

    if not screen.screen_is_valid():
        raise RuntimeError("Screen was not initialised properly")

    debugShader = gl.Shader("default.vert", "default.frag")

    debugShader.use()

    lastX = 0
    lastY = 0
    delta_time = 0.0
    last_time = 0.0
    mouseBound = False
    lastMouse = gl.Screen.PressModes.release
    lastspace = False

    while not screen.should_close():
        # Process time
        current_time = screen.get_time()
        delta_time = current_time - last_time
        last_time = current_time

        screen.poll()

        # Process mouse movement
        xoffset = screen.pos_x - lastX
        yoffset = lastY - screen.pos_y  # reversed since y - coordinates range from bottom to top
        lastX = screen.pos_x
        lastY = screen.pos_y

        # Legacy mouse binding
        if lastMouse == gl.Screen.PressModes.release:
            if screen.get_mouse_state(gl.Screen.MouseButtons.right) == gl.Screen.PressModes.press:
                mouseBound = not mouseBound

        lastMouse = screen.get_mouse_state(gl.Screen.MouseButtons.right)

        # Assorted key checking
        if screen.get_key_state(gl.Screen.Keys.x) == gl.Screen.PressModes.press:
            screen.set_should_close(True)
        if screen.get_key_state(gl.Screen.Keys.Space) == gl.Screen.PressModes.press:
            if lastspace:
                step_mode = "play" if step_mode == "pause" else "pause"  ## Fix only rising edge
            lastspace = False
        else:
            lastspace = True
        if screen.get_key_state(gl.Screen.Keys.Left) == gl.Screen.PressModes.press:
            elapsed_frames -= 1
            key_press_timers[0] = current_time
        if screen.get_key_state(gl.Screen.Keys.Right) == gl.Screen.PressModes.press:
            elapsed_frames += 1
            key_press_timers[1] = current_time

        screen.set_mouse_capture(mouseBound)

        size_x = screen.screen_x
        size_y = screen.screen_y

        # -------------------------------

        aspect = size_y / size_x

        background_color = project.background_color

        # -------------------------------

        screen.set_color(*background_color, 1)
        screen.clear(True, True)

        debugShader.use()
        project.render({"debug_draw_bounds": True, "frames": elapsed_frames, "shader": debugShader, "screen_x": size_x,
                        "screen_y": size_y, "aspect": aspect})
        screen.flip()

        if step_mode == "play":
            elapsed_frames += 1

        # Limit frame rate

    screen.stop()
    return 0


if __name__ == "__main__":
    main()
