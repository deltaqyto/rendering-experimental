import yaml
from scene import Scene
from objects import Object, RectObject, RegPoly, Circle

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