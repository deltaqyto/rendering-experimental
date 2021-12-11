import yaml
import importlib
import bindings as gl
from scene import Scene


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

    def update_object_types(self, types):
        self.object_map.update(types)

    def render(self, passthrough_attribs):
        self.attributes.update(passthrough_attribs)
        self.attributes["shader"] = self.shaders[self.default_shader_name]
        self.attributes["custom_shaders"] = self.shaders
        base_scene = self.scenes["root"].render(self.attributes, self.objects, self.scenes, {**self.shared_data, **self.attributes},
                                                self.setup.get("max_draw_depth", 5), parse_map=self.parse_map, mix_map=self.mix_map)
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
