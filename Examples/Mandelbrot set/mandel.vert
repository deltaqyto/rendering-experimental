#version 330 core

layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 lim;
out vec2 lim_pos;

uniform mat4 matrix;

void main() {
    gl_Position = matrix * vec4(aPos, 0.0, 1.0);
    lim_pos = lim;
}