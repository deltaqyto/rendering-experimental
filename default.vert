#version 330 core
layout (location = 0) in vec2 aPos;// the position variable has attribute position 0

uniform mat4 matrix;
uniform vec3 color;

out vec3 color_o;
out vec2 bPos;

void main()
{
    color_o = color;
    gl_Position = matrix * vec4(aPos, 0.0, 1.0);
    bPos = aPos;
}