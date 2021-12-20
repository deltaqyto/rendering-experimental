import bindings as gl
import math
from attr_handling import parse_attribute_functions, mix_attributes, clip_rects


class Object:
    def __init__(self, name, attributes):
        self.name = name
        self.vao = gl.Vao()
        self.vbo = gl.Vbo()
        self.type = "Undef"
        self.attributes = attributes
        self.default_attrs = {"size_x": [0.5, "horizontal scale factor"], "size_y": [0.5, "vertical scale factor"],
                              "pos_x": [0, "offset from center along x"], "pos_y": [0, "offset from center along y"],
                              "clip_rect": [[-1, -1, 1, 1], "rectangle that marks the drawable border of the object"], "aspect": [1, "aspect ratio"]}

    def __del__(self):
        self.vao.free()
        self.vbo.free()

    def render(self, evaluators, shared_data, external_attrs, parse_map=None, mix_map=None):
        evaluated_attrs = parse_attribute_functions(self.attributes, evaluators, shared_data, parse_map)
        mixed_attrs = mix_attributes(evaluated_attrs, external_attrs, self.default_attrs, mix_map)
        self.draw({**mixed_attrs, **shared_data})

    def pad_list_to_size(self, lst, size, val=0):
        return lst + [val for _ in range(size - len(lst))]

    def get_matrix(self, draw_attrs, enable_pos=True, enable_scale=True):
        matrix = gl.Mat4(1.0)
        if enable_scale:
            matrix = gl.scale(matrix, gl.Vec3(draw_attrs.get("size_x"), draw_attrs.get("size_y"), 1))
        if enable_pos:
            matrix = gl.translate(matrix, gl.Vec3(draw_attrs.get("pos_x"), draw_attrs.get("pos_y"), 0))
        return matrix

    def prep_shader(self, shader, matrix, clip_rect, aspect):
        shader.use()
        shader.setMat4("matrix", matrix)
        shader.setVec4("clip_rect", *clip_rects(*[c for c in clip_rect if c is not None]))
        shader.setFloat("aspect", aspect)

    def draw(self, draw_attrs):
        raise NotImplementedError()

    def mid_render(self, draw_attrs):
        pass

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

        self.default_attrs.update({"color": [(1, 0, 1), "primary color of shape"]})
        self.type = "Rectangle"

    def draw(self, draw_attrs):
        # todo add line_weight, radius
        self.vao.draw_mode(gl.Vao.Modes.fill)

        color = draw_attrs.get("color")

        matrix = self.get_matrix(draw_attrs)

        self.prep_shader(draw_attrs.get("shader"), matrix, draw_attrs.get("clip_rect"), draw_attrs.get("aspect"))
        draw_attrs.get("shader").setVec3("color", *color)

        self.mid_render(draw_attrs)

        self.vao.draw_verts(0, 0, True)


class RegPoly(Object):
    def __init__(self, name, attributes):
        super().__init__(name, attributes)
        self.vao.set_row_size(2)
        self.vao.assign_data(0, 2)
        self.ebo = gl.Ebo()

        self.default_attrs.update({"color": [(1, 0, 1), "primary color of shape"], "faces": [4, "number of sides on polygon"],
                                   "max_faces": [64, "largest number of faces the shape can have"]})

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
        self.vertices = [0, 0] + self.distribute(draw_attrs.get("size_x"), draw_attrs.get("size_y"), faces)
        self.indices = self.tri_fan_indices(faces)

        self.vertices = self.pad_list_to_size(self.vertices, draw_attrs.get("max_faces") * 2 + 2)
        self.indices = self.pad_list_to_size(self.indices, draw_attrs.get("max_faces") * 3)

        self.vbo.add_data(self.vertices, gl.GL_const.dynamic_draw)
        self.ebo.add_data(self.indices, gl.GL_const.dynamic_draw)

        self.vao.draw_mode(gl.Vao.Modes.fill)

        matrix = self.get_matrix(draw_attrs)

        self.prep_shader(draw_attrs.get("shader"), matrix, draw_attrs.get("clip_rect"), draw_attrs.get("aspect"))
        draw_attrs.get("shader").setVec3("color", *draw_attrs.get("color"))

        self.mid_render(draw_attrs)

        self.vao.draw_elements(0, 0, True)


class Circle(RegPoly):
    def __init__(self, name, attributes):
        super().__init__(name, attributes)
        self.default_attrs["faces"][0] = self.default_attrs["max_faces"][0]  # At faces > 20 looks like a circle enough


class ShadedRect(Object):
    def __init__(self, name, attributes):
        super().__init__(name, attributes)

        self.vao.set_row_size(4)
        self.vao.assign_data(0, 2)
        self.vao.assign_data(1, 2)

        self.ebo = gl.Ebo()

        self.vertices = [-1, -1, 1, 1, -1, 1, 1, -1]
        self.indices = [0, 1, 2, 0, 3, 1]

        self.ebo.add_data(self.indices, gl.GL_const.static_draw)
        self.vbo.add_data(self.vertices, gl.GL_const.dynamic_draw)

        self.vao.add_vbo(self.vbo)
        self.vao.add_ebo(self.ebo)

        self.default_attrs.update({"shader_name": ["default", "name of shader to use"],
                                   "uv_coords": [[2, 2, 0, 0], "corners of the drawn region, passed to the shader as uv_coords"]})
        self.type = "Shaded Rectangle"

    def zip_coords(self, v1, v2):
        # First create pairs of 2 items out of both v1 and v2. Zip these, then apply two layers of flattening
        return [w for e in [i for q in zip([(v1[2 * m], v1[2 * m + 1]) for m in range(round(len(v1) / 2))],
                                           [(v2[2 * n], v2[2 * n + 1]) for n in range(round(len(v2) / 2))]) for i in q] for w in e]

    def convert_dims_to_rect_verts(self, dims):
        out = [-dims[0] + dims[2], -dims[1] + dims[3], dims[0] + dims[2], dims[1] + dims[3],
               -dims[0] + dims[2], dims[1] + dims[3], dims[0] + dims[2], -dims[1] + dims[3]]
        return out

    def __del__(self):
        self.ebo.free()
        super().__del__()

    def draw(self, draw_attrs):
        self.vao.draw_mode(gl.Vao.Modes.fill)

        matrix = self.get_matrix(draw_attrs)
        self.prep_shader(draw_attrs.get("shader"), matrix, draw_attrs.get("clip_rect"), draw_attrs.get("aspect"))

        self.vbo.add_data(self.zip_coords(self.vertices, self.convert_dims_to_rect_verts(draw_attrs.get("uv_coords"))), gl.GL_const.dynamic_draw)

        self.mid_render(draw_attrs)

        self.vao.draw_elements(0, 0, True)


class FractalRenderer(ShadedRect):
    def __init__(self, name, attributes):
        super().__init__(name, attributes)
        self.type = "Fractal Rectangle"
        self.default_attrs["max_iters"] = [20, "maximum iteration count"]

    def draw(self, draw_attrs):
        self.vao.draw_mode(gl.Vao.Modes.fill)
        self.vbo.add_data(self.zip_coords(self.vertices, self.convert_dims_to_rect_verts(draw_attrs.get("uv_coords"))), gl.GL_const.dynamic_draw)

        matrix = self.get_matrix(draw_attrs)
        self.prep_shader(draw_attrs.get("custom_shaders").get(draw_attrs.get("shader_name")), matrix,
                         draw_attrs.get("clip_rect"), draw_attrs.get("aspect"))

        self.mid_render(draw_attrs)

        self.vao.draw_elements(0, 0, True)

    def mid_render(self, draw_attrs):
        draw_attrs.get("custom_shaders").get(draw_attrs.get("shader_name")).setInt("iterations_max", round(draw_attrs.get("max_iters")))
        draw_attrs.get("custom_shaders").get(draw_attrs.get("shader_name")).setInt("screen_x", draw_attrs.get("screen_x"))
        draw_attrs.get("custom_shaders").get(draw_attrs.get("shader_name")).setInt("screen_y", draw_attrs.get("screen_y"))
