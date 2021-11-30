import pygame
import sys
import yaml
import time
import math


def parse_attribute_functions(attribs, eval_vals, debug=False):
    if not attribs:
        return {}
    mappings = {"const": lambda _, vals: vals[0], "linear_frames": lambda evals, vals: vals[0] * eval_vals.get("frames", 1),
                "const_vec3": lambda _, vals: vals[:3]}
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

    def get_blank(self, size, chroma_col):
        image = pygame.Surface(size)
        image.fill(chroma_col)
        return image

    def render(self, attributes):
        raise NotImplementedError()

    def __repr__(self):
        return f"Generic object {self.name}"


class RectObject(Object):
    def __init__(self, name):
        super().__init__(name)

    def __repr__(self):
        return f"Rectangle object {self.name}"

    def render(self, attributes):
        aa_scale = attributes.get("aa_scale", 1)
        size = (attributes.get("width", 40), attributes.get("height", 40))
        blank = self.get_blank(((aa_scale * size[0] + attributes.get("line_weight", 2) + 1),
                                (aa_scale * size[1] + attributes.get("line_weight", 2) + 1)),
                               attributes.get("chroma_col", (255, 0, 255)))
        pygame.draw.rect(blank, attributes.get("color", "blue"), (0, 0, aa_scale * size[0], aa_scale * size[1]),
                         attributes.get("line_weight", 2), attributes.get("radius", -1))
        blank.set_colorkey(attributes.get("chroma_col", (255, 0, 255)))
        blank = pygame.transform.scale(blank.convert_alpha(), size)

        return blank


class CircleObject(Object):
    def __init__(self, name):
        super().__init__(name)

    def __repr__(self):
        return f"Circle object {self.name}"

    def render(self, attributes):
        aa_scale = attributes.get("aa_scale", 1)
        size = (2 * attributes.get("radius", 40), 2 * attributes.get("radius", 40)) if attributes.get("autofit", False) \
            else (2 * attributes.get("width", 40), 2 * attributes.get("height", 40))
        blank = self.get_blank((aa_scale * size[0], aa_scale * size[1]), attributes.get("chroma_col", (255, 0, 255)))
        pygame.draw.circle(blank, attributes.get("color", "red"),
                           (attributes.get("pos_x", 0) + attributes.get("radius", 40),
                            attributes.get("pos_y", 0) + aa_scale * attributes.get("radius", 40)),
                           aa_scale * attributes.get("radius", 40), attributes.get("line_weight", 2))
        blank.set_colorkey(attributes.get("chroma_col", (255, 0, 255)))
        blank = pygame.transform.smoothscale(blank.convert_alpha(), size)
        return blank


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

    def get_blank(self, size, chroma_col):
        image = pygame.Surface(size)
        image.fill(chroma_col)
        return image

    def render(self, attributes, object_cache, scene_cache, scenes):
        self_attrs = parse_attribute_functions({**attributes, **self.self_attrs}, attributes)
        size_cache = [0, 0]

        obj_attr_cache = {}
        for name, item in self.obj_children.items():
            obj_attr_cache[name] = parse_attribute_functions(item, self_attrs)
            size_cache = [max(a + c, b) for a, b, c in zip(object_cache[name].get_size(), size_cache,
                                                           (obj_attr_cache[name].get("pos_x", 0), obj_attr_cache[name].get("pos_y", 0)))]
            # Get size info here

        sc_attr_cache = {}
        for name, scene in self.sc_children.items():
            mods = parse_attribute_functions(scene, self_attrs)
            new_attr = {**self_attrs, **mods}
            sc_attr_cache[name] = new_attr
            if name not in scene_cache:
                scene_cache[name] = scenes[name].render(new_attr, object_cache, scene_cache, scenes)
            size_cache = [max(a + c, b) for a, b, c in zip(scene_cache[name].get_size(), size_cache,
                                                           (sc_attr_cache[name].get("pos_x", 0), sc_attr_cache[name].get("pos_y", 0)))]

        size = size_cache if self_attrs.get("autofit", False) \
            else (self_attrs.get("width", 400), self_attrs.get("height", 400))
        blank_col = self_attrs.get("background_col", (100, 0, 0)) if self_attrs.get("use_background", False) \
            else self_attrs.get("chroma_col", (255, 0, 255))
        blank = self.get_blank(size, blank_col)

        for name, item in self.obj_children.items():
            blank.blit(object_cache[name], (obj_attr_cache[name].get("pos_x", 0), obj_attr_cache[name].get("pos_y", 0)))

        for name, scene in self.sc_children.items():
            blank.blit(scene_cache[name], (sc_attr_cache[name].get("pos_x", 0), sc_attr_cache[name].get("pos_y", 0)))

        blank.set_colorkey(self_attrs.get("chroma_col", (255, 0, 255)))
        if self_attrs.get("debug_draw_bounds", False):
            pygame.draw.rect(blank, "purple", (0, 0, size[0] - 2, size[1] - 2), 2)
        return blank

    def __repr__(self):
        return f"Scene {self.name}"


class Project:
    def __init__(self, name):
        self.name = name
        self.scenes = {}
        self.objects = []
        self.attributes = {}
        self.setup = {}
        self.object_types = {"rect": RectObject, "circle": CircleObject}

    def update_object_types(self, types):
        self.object_types.update(types)

    def render(self, passthrough_attribs):
        self.attributes.update(passthrough_attribs)
        object_results = {obj.name: obj.render({**self.attributes, **parse_attribute_functions(attr, self.attributes)}) for obj, attr in self.objects}
        base_scene = self.scenes["root"].render(self.attributes, object_results, {}, self.scenes)
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
    x_size = round(720 * scale)
    y_size = round(480 * scale)

    project = Project("base")
    project.load("debug.yaml")
    print(project.scenes, project.objects)

    pygame.init()
    screen = pygame.display.set_mode((x_size, y_size))
    pygame.display.set_caption('Editor')
    clock = pygame.time.Clock()
    frame_rate = project.setup["frame_rate"]
    elapsed_frames = 0

    step_mode = "play"
    scrubbing_repeat_time = 0.1
    key_press_timers = [0, 0]

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    step_mode = "play" if step_mode == "pause" else "pause"

        keys = pygame.key.get_pressed()
        if keys[pygame.K_q] or keys[pygame.K_x]:
            pygame.quit()
            sys.exit()
        if keys[pygame.K_LEFT] and time.time() - key_press_timers[0] > scrubbing_repeat_time:
            elapsed_frames -= 1
            key_press_timers[0] = time.time()
        if keys[pygame.K_RIGHT] and time.time() - key_press_timers[1] > scrubbing_repeat_time:
            elapsed_frames += 1
            key_press_timers[1] = time.time()

        screen.fill("white")
        screen.blit(project.render({"chroma_col": (255, 0, 255), "debug_draw_bounds": True, "frames": elapsed_frames}), (0, 0))
        pygame.display.flip()
        if step_mode == "play":
            elapsed_frames += 1
        clock.tick(frame_rate)


if __name__ == "__main__":
    main()
