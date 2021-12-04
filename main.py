import math
import yaml
import bindings as gl


def parse_attribute_functions(attribs, eval_vals, debug=False):
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


class Object:
    def __init__(self, name):
        self.name = name
        self.vao = gl.Vao()
        self.vbo = gl.Vbo()

        self.type = "Undef"
        self.attributes = []

    def __del__(self):
        self.vao.free()
        self.vbo.free()

    def render(self, attributes):
        raise NotImplementedError()

    def __repr__(self):
        return f"Generic object {self.name}"

    def list_attributes(self):
        print(f"{self.type} object: {self.name}")
        for attr in self.attributes:
            print(f"{attr[0]}, assume {attr[1]}, {attr[2]}")
        print()


class RectObject(Object):
    def __init__(self, name):
        super().__init__(name)
        self.vao.set_row_size(2)
        self.vao.assign_data(0, 2)
        self.vertices = [-1.0, -1.0, 1.0, 1.0, -1.0, 1.0,
                         -1.0, -1.0, 1.0, -1.0, 1.0, 1.0]
        self.vbo.add_data(self.vertices, gl.GL_const.static_draw)
        self.vao.add_vbo(self.vbo)

        self.attributes = [("width", 40, "width of shape in pixels")]
        self.type = "Rect"

    def __repr__(self):
        return f"Rectangle object {self.name}"

    def render(self, attributes):

        # line_weight, radius
        matrix = gl.Mat4(1.0)
        matrix = gl.translate(matrix, gl.Vec3(attributes.get("pos_x", 0), attributes.get("pos_y", 0), 0))
        matrix = gl.scale(matrix, gl.Vec3(attributes.get("size_x", 0.5), attributes.get("size_y", 0.5), 1))

        self.vao.draw_mode(gl.Vao.Modes.fill)

        color = attributes.get("color", (1, 0, 1))

        attributes.get("shader").setMat4("matrix", matrix)
        attributes.get("shader").setVec3("color", *color)

        self.vao.draw_verts(0, 0, True)
        return 0


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

    def render(self, attributes, objects, scenes):
        self_attrs = parse_attribute_functions({**attributes, **self.self_attrs}, attributes)
        size_cache = [0, 0]

        obj_attr_cache = {}
        for name, item in self.obj_children.items():
            obj_attr_cache[name] = parse_attribute_functions(item, self_attrs)

        sc_attr_cache = {}
        for name, scene in self.sc_children.items():
            mods = parse_attribute_functions(scene, self_attrs)
            new_attr = {**self_attrs, **mods}
            sc_attr_cache[name] = new_attr
            scenes[name].render(new_attr, objects, scenes)

        size = size_cache if self_attrs.get("autofit", False) \
            else (self_attrs.get("width", 400), self_attrs.get("height", 400))
        blank_col = self_attrs.get("background_col", (100, 0, 0)) if self_attrs.get("use_background", False) \
            else self_attrs.get("chroma_col", (255, 0, 255))

        #if self_attrs.get("debug_draw_bounds", False):
        #    pygame.draw.rect(blank, "purple", (0, 0, size[0] - 2, size[1] - 2), 2)
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
        self.object_types = {"rect": RectObject}

    def update_object_types(self, types):
        self.object_types.update(types)

    def render(self, passthrough_attribs):
        self.attributes.update(passthrough_attribs)
        object_results = {obj.name: obj.render({**self.attributes, **parse_attribute_functions(attr, self.attributes)}) for obj, attr in self.objects}
        base_scene = self.scenes["root"].render(self.attributes, self.objects, self.scenes)
        return base_scene

    def load(self, file_name):
        """
        Load in all scenes and objects, assign relations to each node
        """
        self.scenes = {}
        self.objects = []
        self.setup = {}
        with open(file_name) as file:
            data = yaml.load(file, Loader=yaml.FullLoader)
            scenes = data["graph"]["scenes"]
            objects = data["graph"]["objects"]
            self.setup = data["setup"]
            self.objects = [[self.object_types.get(obj["type"])(name), obj] for name, obj in objects.items()]
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
            step_mode = "play" if step_mode == "pause" else "pause"      ## Fix only rising edge
        if screen.get_key_state(gl.Screen.Keys.Left) == gl.Screen.PressModes.press:
            elapsed_frames -= 1
            key_press_timers[0] = current_time
        if screen.get_key_state(gl.Screen.Keys.Right) == gl.Screen.PressModes.press:
            elapsed_frames += 1
            key_press_timers[1] = current_time

        screen.set_mouse_capture(mouseBound)

        # -------------------------------
        screen.set_color(0.2, 0.3, 0.3, 1)
        screen.clear(True, True)

        debugShader.use()
        project.render({"chroma_col": (255, 0, 255), "debug_draw_bounds": True, "frames": elapsed_frames, "shader": debugShader, "screen_x":size_x, "screen_y":size_y})

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
