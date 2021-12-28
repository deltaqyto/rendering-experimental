from attr_handling import parse_attribute_functions, mix_attributes, clip_rects


# todo possibly make the bounding boxes shrink fit


class Scene:
    def __init__(self, name, sc_children=None, obj_children=None, self_attrs=None):
        self.sc_children = sc_children if sc_children is not None else []
        self.obj_children = obj_children if obj_children is not None else []
        self.attributes = self_attrs if self_attrs is not None else {}
        self.name = name

        self.past_rect = [0, 0, 0, 0]
        self.past_aspect = 1

        self.default_attrs = {"size_x": [1, "horizontal scale factor"], "size_y": [1, "vertical scale factor"],
                              "clip_size_x": [1, "size of clip rect along x"], "clip_size_y": [1, "size of clip rect along y"],
                              "pos_x": [0, "offset from center along x"], "pos_y": [0, "offset from center along y"],
                              "clip_rect": [[-1, -1, 1, 1], "rectangle that marks the drawable border of the scene"], "aspect": [1, "aspect ratio"]}

    def collision_test(self, point, scenes, objects, in_name=""):
        in_name = self.name if self.past_rect[0] < point[0] * self.past_aspect < self.past_rect[2] and \
                               self.past_rect[1] < point[1] < self.past_rect[3] else in_name
        # for object
        for obj in self.obj_children:
            in_name = objects[obj].collision_test(point, in_name)

        # for scene
        for scn in self.sc_children:
            in_name = scenes[scn].collision_test(point, scenes, objects, in_name)

        return in_name

    def add_scene(self, child):
        self.sc_children.append(child)

    def add_object(self, child):
        self.obj_children.append(child)

    def render(self, evaluators, objects, scenes, shared_data, depth, external_attrs=None, parse_map=None, mix_map=None):
        external_attrs = {} if external_attrs is None else external_attrs
        evaluated_attrs = parse_attribute_functions(self.attributes, evaluators, shared_data, parse_map)
        mixed_attrs = mix_attributes(evaluated_attrs, external_attrs, self.default_attrs, mix_map)
        self.draw(objects, scenes, {**mixed_attrs, **shared_data}, evaluators, shared_data, depth, parse_map, mix_map)

    def draw(self, objects, scenes, inheritables, evaluators, shared_data, depth, parse_map, mix_map):
        gen_clip_rect = [- inheritables["clip_size_x"] * inheritables["size_x"], - inheritables["clip_size_y"] * inheritables["size_y"],
                         inheritables["clip_size_x"] * inheritables["size_x"], inheritables["clip_size_y"] * inheritables["size_y"]]
        inheritables["clip_rect"] = clip_rects(gen_clip_rect, *[i for i in inheritables["clip_rect"] if i is not None])

        # Cache data
        self.past_rect = inheritables["clip_rect"]
        self.past_aspect = inheritables["aspect"]

        # Render all objects
        for name in self.obj_children:
            if name not in objects:
                print("skip")
                continue
            objects[name].render(evaluators, shared_data, inheritables, parse_map, mix_map)

        # Render all scenes
        if depth < 0:
            return
        for name in self.sc_children:
            if name not in scenes:
                continue
            scenes[name].render(evaluators, objects, scenes, shared_data, depth - 1, inheritables, parse_map, mix_map)

    def __repr__(self):
        return f"Scene {self.name}"