#version 330 core
layout (location = 0) in vec2 aPos;

uniform mat4 matrix;
uniform vec3 color;
uniform float aspect;

out vec3 color_o;
out vec2 bPos;

void main()
{
    color_o = color;
    gl_Position = matrix * vec4(aPos, 0.0, 1.0);
    gl_Position = vec4(gl_Position.x * aspect, gl_Position.y, gl_Position.zw);
    bPos = gl_Position.xy;
}