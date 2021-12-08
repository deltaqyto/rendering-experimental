import math
import yaml
import bindings as gl


def parse_attribute_functions(attribs, eval_vals, shared_data, debug=False):
    if not attribs:
        return {}
    mappings = {"const": lambda _, vals: vals[0], "linear_frames": lambda evals, vals: vals[0] * evals.get("frames", 1),
                "const_vec3": lambda _, vals: vals[:3], "sin": lambda evals, vals: vals[1] * math.sin(vals[0] * evals.get("frames", 1)),
                "sin_offset": lambda evals, vals: vals[1] * math.sin(vals[2] + vals[0] * evals.get("frames", 1))}
    new_attribs = {}
    for name, attrib in attribs.items():
        try:
            temp = mappings.get(attrib[0])
        except TypeError:
            new_attribs[name] = attrib
            continue
        if temp is None:
            continue
        attrib = temp(eval_vals, attrib[1:])
        new_attribs[name] = attrib
    if debug is True:
        print(attribs, eval_vals, new_attribs)
    return new_attribs


def mix_attributes(attrib_set_1, attrib_set_2, default_attrs):
    """Each name in default_attrs is returned with a value derived from attrib sets 1 and 2.
    Mix behaviors allows selection of the mix type for different names"""
    mix_behaviours = {"alpha": "mult", "pos_x": "add", "pos_y": "add", "visible": "inherit", "unused": "ignore"}   # Should "inherit" by default
    out_attrs = {}
    for name, attr in default_attrs.items():
        mode = mix_behaviours.get(name, "inherit")
        if mode == "mult":
            out_attrs[name] = attrib_set_1[name] * attrib_set_2[name] if name in attrib_set_1 and name in attrib_set_2 else attr[0]
        elif mode == "add":
            out_attrs[name] = attrib_set_1[name] + attrib_set_2[name] if name in attrib_set_1 and name in attrib_set_2 else attr[0]

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
        return f"Generic object {self.name}"

    def list_attributes(self):
        print(f"{self.type} object: {self.name}")
        for name, attr in self.attributes.items():
            print(f"{name}, assume {attr[1]}, {attr[2]}")
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
        self.type = "Rect"

    def __repr__(self):
        return f"Rectangle object {self.name}"

    def draw(self, draw_attrs):

        # line_weight, radius
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
        print(self.default_attrs["faces"])

        self.vbo.add_data(self.vertices, gl.GL_const.dynamic_draw)
        self.ebo.add_data(self.indices, gl.GL_const.dynamic_draw)

        self.vao.add_vbo(self.vbo)
        self.vao.add_ebo(self.ebo)

        self.type = "RegPolygon"

    def __repr__(self):
        return f"Regular polygon object {self.name}"

    def distribute(self, a, b, num):
        """Get intersection point of a line y = mx and ellipse x^2/a^2 + y^2/b^2 = 1, for num points spaced with equal separation angles """
        out_points = []
        divisor = 2 * math.pi / num
        for cur in range(num):
            m = divisor * cur
            if m == math.pi / 2:
                out_points += [0, b]
                continue
            if m == 3 * math.pi/2:
                out_points += [0, -b]
                continue
            multiplier = 1 if 0 <= m < math.pi/2 or 3 * math.pi/2 < m <= 2 * math.pi else -1
            m = math.tan(m)
            intersection = [((a*a * b*b)/(a*a * m*m + b*b)) ** 0.5 * multiplier, 0]
            intersection[1] = m * intersection[0]
            out_points += intersection
        return out_points

        #todo add catch case where gradient is infinity, in which case intersection is (0, +-b)

    def tri_fan_indices(self, num):
        output = []
        for count in range(num):
            output += [0, count + 1, count + 2]
        if output:
            output[-1] = 1
        return output
            
    def __del__(self):
        self.ebo.free()
        super().__del__()

    def draw(self, draw_attrs):

        self.vertices = [0, 0] + self.distribute(0.8, 0.8, draw_attrs.get("faces"))
        self.indices = self.tri_fan_indices(draw_attrs.get("faces"))

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
        self.default_attrs["faces"][0] = 40



class Scene:
    def __init__(self, name, sc_children=None, obj_children=None, self_attrs=None):
        self.sc_children = sc_children if sc_children is not None else {}
        self.obj_children = obj_children if obj_children is not None else {}
        self.self_attrs = self_attrs if self_attrs is not None else {}
        self.name = name

    def add_scene(self, child):
        self.sc_children.append(child)

    def add_object(self, child):
        self.obj_children.append(child)

    def render(self, attributes, objects, scenes, shared_data, parent_attrs=None):

        # todo restructure to move shaders and stuff into the shared data, and are now part of the expected values

        # Calculate inheritables
        parent_attrs = {} if parent_attrs is None else parent_attrs
        inheritables = parse_attribute_functions(self.self_attrs, attributes, shared_data)

        # Render all objects
        for name, obj_attrs in self.obj_children.items():
            if name not in objects:
                print("skip")
                continue
            objects[name].render(attributes, shared_data, inheritables)

        # Render all scenes
        for name, scene_attrs in self.sc_children.items():
            if name not in scenes:
                continue
            scenes[name].render(attributes, objects, scenes, shared_data)

        return 0

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

    def update_object_types(self, types):
        self.object_types.update(types)

    def render(self, passthrough_attribs):
        self.attributes.update(passthrough_attribs)
        base_scene = self.scenes["root"].render(self.attributes, self.objects, self.scenes, {**self.shared_data, **self.attributes})
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
            scenes = data["graph"]["scenes"]
            objects = data["graph"]["objects"]
            self.shared_data = data["shared_data"]
            self.setup = data["setup"]
            self.objects = {name: self.object_types.get(obj["type"])(name, obj) for name, obj in objects.items()}
            self.scenes = {name: Scene(name, sc["scenes"], sc["objects"], sc["self"]) for name, sc in scenes.items()}


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
        raise RuntimeError("WadSDSD")

    tex1 = gl.Texture("container.jpg", gl.Texture.Color_modes.rgb)

    tex2 = gl.Texture("awesomeface.png", gl.Texture.Color_modes.rgba)

    debugShader = gl.Shader("default.vert", "default.frag")

    debugShader.use()

    lastX = 0
    lastY = 0
    delta_time = 0.0
    last_time = 0.0
    mouseBound = False
    lastMouse = gl.Screen.PressModes.release

    while not screen.should_close():
        current_time = screen.get_time()
        delta_time = current_time - last_time
        last_time = current_time

        screen.poll()

        xoffset = screen.pos_x - lastX
        yoffset = lastY - screen.pos_y  # reversed since y - coordinates range from bottom to top
        lastX = screen.pos_x
        lastY = screen.pos_y

        if lastMouse == gl.Screen.PressModes.release:
            if screen.get_mouse_state(gl.Screen.MouseButtons.right) == gl.Screen.PressModes.press:
                mouseBound = not mouseBound

        lastMouse = screen.get_mouse_state(gl.Screen.MouseButtons.right)

        if screen.get_key_state(gl.Screen.Keys.x) == gl.Screen.PressModes.press:
            screen.set_should_close(True)
        if screen.get_key_state(gl.Screen.Keys.Space) == gl.Screen.PressModes.press:
            step_mode = "play" if step_mode == "pause" else "pause"  ## Fix only rising edge
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

        # -------------------------------
        screen.set_color(0.2, 0.3, 0.3, 1)
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

    # gl.main(screen)


main()

'''for l in [cubePositions[i:i + 3] for i in range(0, len(cubePositions), 3)]:
        l = [str(q) for q in l]
        print(", ".join(l) + ",") '''
