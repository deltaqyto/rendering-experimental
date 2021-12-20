#version 330 core
out vec4 FragColor;

in vec3 color_o;
in vec2 bPos;
uniform vec4 clip_rect;

void main()
{
    FragColor = vec4(color_o, 1.0);
    if (bPos.x < clip_rect.x || bPos.x > clip_rect.z || bPos.y < clip_rect.y || bPos.y > clip_rect.w){
        discard;
    }
}