#version 330 core
layout (location = 0) in vec3 aPos;// the position variable has attribute position 0
layout (location = 1) in vec3 aCol;
layout (location = 2) in vec2 aTexCoord;

uniform float green;
out vec3 vertexColor;
out vec2 TexCoord;

uniform mat4 model;
uniform mat4 view;
uniform mat4 projection;

void main()
{
    gl_Position = projection * view * model * vec4(aPos, 1.0);// see how we directly give a vec3 to vec4's constructor
    vertexColor = vec3(aCol.x, green, aCol.z);
    TexCoord = aTexCoord;
}