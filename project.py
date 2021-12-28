import yaml
import importlib
import bindings as gl
from scene import Scene
from editor import Editor


class Project:
    def __init__(self, name):
        self.name = name
        self.scenes = {}
        self.objects = []
        self.attributes = {}
        self.setup = {}
        self.shared_data = {}
        self.object_map = {}
        self.background_color = [0, 0, 0]

        self.parse_map = {}
        self.mix_map = {}
        self.shaders = {}
        self.default_shader_name = "default"

        self.target_scene = "root"
        self.edit = False
        self.editor = Editor()

    def update_object_types(self, types):
        self.object_map.update(types)

    def enable_edit(self):
        self.edit = True
        self.target_scene = self.editor.editor_name

    def disable_edit(self):
        self.edit = False
        self.target_scene = "root"

    def render(self, passthrough_attribs):
        self.attributes.update(passthrough_attribs)
        self.attributes["shader"] = self.shaders[self.default_shader_name]
        self.attributes["custom_shaders"] = self.shaders

        if self.edit:
            self.scenes.update(self.editor.get_editor_scenes())
            self.objects.update(self.editor.get_editor_objects())  # Objects reserved by the editor will be prefixed with edt_. Avoid clashes

        base_scene = self.scenes[self.target_scene].render(self.attributes, self.objects, self.scenes, {**self.shared_data, **self.attributes},
                                                           self.setup.get("max_draw_depth", 5), parse_map=self.parse_map, mix_map=self.mix_map)
        if self.edit:
            self.editor.update(self.attributes, self.scenes, self.objects)

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
            self.data_backup = data

            # Handy contractions
            scenes = data["graph"]["scenes"]
            objects = data["graph"]["objects"]

            # Save to project memory
            self.shared_data = data["shared_data"]
            self.setup = data["setup"]
            self.default_shader_name = data["setup"].get("default_shader_name", "default")

            for map_file in data.get("maps", []):
                module = importlib.import_module(map_file)
                maps = getattr(module, "get_maps")()
                self.parse_map.update(maps.get("parse", {}))
                self.mix_map.update(maps.get("mix", {}))
                self.object_map.update(maps.get("objects", {}))

            for name, shaders in data.get("shaders", {}).items():
                # Infer the type of shaders via starter string
                shader_ext = {"v": ".vert", "f": ".frag", "t": ".tess", "g": ".geom"}
                shader_modes = {"v": gl.Shader.program_types.vertex, "f": gl.Shader.program_types.fragment,
                                "g": gl.Shader.program_types.geometry}
                shader_blank = gl.Shader()
                for type, text in zip(shaders[0], shaders[1:]):
                    if text[-5:] == ".file":
                        shader_text = open(text[:-5] + shader_ext[type], "r").read()
                    else:
                        shader_text = text

                    shader_blank.compile(shader_modes[type], shader_text)
                shader_blank.link()

                self.shaders[name] = shader_blank

            # Process object and scene dictionaries
            self.objects = {name: self.object_map.get(obj["type"])(name, obj) for name, obj in objects.items()}
            self.scenes = {name: Scene(name, sc["scenes"], sc["objects"], sc["self"]) for name, sc in scenes.items()}

        self.background_color = self.shared_data.get("background", [0, 0, 0])
