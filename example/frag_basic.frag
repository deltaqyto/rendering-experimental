#version 330 core
out vec4 FragColor;
in vec3 vertexColor;
in vec2 TexCoord;

uniform sampler2D texture1;
uniform sampler2D texture2;
uniform float mix;

void main()
{
    FragColor = mix(texture(texture1, 2 * TexCoord), texture(texture2, vec2(-TexCoord.x, TexCoord.y)), mix);
}