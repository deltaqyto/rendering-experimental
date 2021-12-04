#version 330 core
out vec4 FragColor;

in vec3 color_o;

void main()
{
    FragColor = vec4(color_o, 1.0);
}