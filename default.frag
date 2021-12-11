#version 330 core
out vec4 FragColor;

in vec3 color_o;
in vec2 bPos;
uniform vec4 clip_bounds;

void main()
{
    FragColor = vec4(color_o, 1.0);
    if (!(bPos.x >= clip_bounds.x && bPos.x <= clip_bounds.z && bPos.y >= clip_bounds.y && bPos.y <= clip_bounds.w)){
        discard;
    }
}