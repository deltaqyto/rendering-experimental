#version 330 core

layout (location = 0) in vec2 aPos;
layout (location = 1) in vec2 lim;
out vec2 lim_pos;
out vec2 bPos;

uniform mat4 matrix;
uniform float aspect;

void main() {
    lim_pos = lim;

    gl_Position = matrix * vec4(aPos, 0.0, 1.0);
    gl_Position = vec4(gl_Position.x * aspect, gl_Position.yzw);
    bPos = gl_Position.xy;
}