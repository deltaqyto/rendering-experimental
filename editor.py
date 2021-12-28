from scene import Scene
from objects import RectObject


# todo begin work on a widgets library. Perhaps some resizing handles are a good start.
# todo recursive render depth offset in the editor
class Editor:
    def __init__(self):
        self.editor_name = "editor"
        self.editor_prefix = "edt_"

        self.preview_size = 0.5
        self.preview_boundary_weight = 0.01

        self.master_scene = Scene(self.editor_name, [self.editor_prefix + "preview_wrapper"], [], {"size_x": ["const", 1], "size_y": ["const", 1]})
        self.objects = {self.editor_prefix + "preview_bounding_box": RectObject(self.editor_prefix + "preview_bounding_box",
                                                                                {"size_x": ["inv_aspect"], "size_y": ["const", 1],
                                                                                 "line_weight": ["const", self.preview_boundary_weight * 2],
                                                                                 "edge_mode": ["const", "standard"],
                                                                                 "color": [[3, "const"], 1, 0, 0]})}

        self.scenes = {self.editor_name: self.master_scene,
                       self.editor_prefix + "preview_wrapper": Scene(self.editor_prefix + "preview_wrapper",
                                                                     [self.editor_prefix + "preview_container"],
                                                                     [self.editor_prefix + "preview_bounding_box"],
                                                                     {"size_x": ["const", self.preview_size + self.preview_boundary_weight],
                                                                      "size_y": ["const", self.preview_size + self.preview_boundary_weight]}),
                       self.editor_prefix + "preview_container": Scene(self.editor_prefix + "preview_container", ["root"], [],
                                                                       {"size_x": ["const", self.preview_size / (
                                                                                   self.preview_size + self.preview_boundary_weight)],
                                                                        "size_y": ["const", self.preview_size / (
                                                                                    self.preview_size + self.preview_boundary_weight)]})
                       }

        # Selection variables
        self.current_targets = []  # Index 0 is given priority

    def get_editor_scenes(self) -> dict:
        return self.scenes

    def get_editor_objects(self) -> dict:
        return self.objects

    def update(self, attributes, current_scene, current_objects):
        lmouse_press = attributes.get("mouse_press")[0]
        # Find any objects/scenes under by the mouse
        target = current_scene["root"].collision_test([attributes["mouse_x"] / attributes["aspect"], attributes["mouse_y"]],
                                                      current_scene, current_objects)
        if lmouse_press:
            if target in self.current_targets:
                self.current_targets.remove(target)
            else:
                self.current_targets.insert(0, target)

        print(self.current_targets)


class SelectionHandle:
    def __init__(self):
        self.bounds = [0, 0, 1, 1]
