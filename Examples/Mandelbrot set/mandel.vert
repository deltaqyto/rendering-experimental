#version 330 core

layout (location = 0) in vec2 aPos;// the position variable has attribute position 0
out vec2 tpos;

uniform mat4 matrix;

void main() {
    gl_Position = matrix * vec4(aPos, 0.0, 1.0);
    tpos = aPos;
}