from scene import Scene
from objects import RectObject


# todo allow for a rectangular frame
# todo begin work on a widgets library. Perhaps some resizing handles are a good start.

class Editor:
    def __init__(self):
        self.editor_name = "editor"
        self.editor_prefix = "edt_"

        self.preview_size = 0.5
        self.preview_boundary_weight = 0.02

        self.master_scene = Scene(self.editor_name, [self.editor_prefix + "preview_wrapper"], [], {"size_x": ["const", 1], "size_y": ["const", 1]})
        self.objects = {self.editor_prefix + "preview_bounding_box": RectObject(self.editor_prefix + "preview_bounding_box",
                                                                                {"size_x": ["const", 1], "size_y": ["const", 1],
                                                                                 "line_weight": ["const", self.preview_boundary_weight]})}

        self.scenes = {self.editor_name: self.master_scene,
                       self.editor_prefix + "preview_wrapper": Scene(self.editor_name, [self.editor_prefix + "preview_container"], [],
                                                                     {"size_x": ["const", self.preview_size + self.preview_boundary_weight],
                                                                      "size_y": ["const", self.preview_size + self.preview_boundary_weight]}),
                       self.editor_prefix + "preview_container": Scene(self.editor_prefix + "preview_container", ["root"], [],
                                                                       {"size_x": ["const", 1 - self.preview_boundary_weight],
                                                                        "size_y": ["const", 1 - self.preview_boundary_weight]})
                       }
        self.scenes[self.editor_prefix + "preview_wrapper"].add_object(self.editor_prefix + "preview_bounding_box")

    def get_editor_scenes(self) -> dict:
        return self.scenes

    def get_editor_objects(self) -> dict:
        return self.objects
