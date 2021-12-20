#version 330 core


in vec2 lim_pos;
in vec2 bPos;
out vec4 frag_color;

uniform int iterations_max;

uniform int screen_x;
uniform int screen_y;
uniform vec4 clip_bounds;

#define supersample 4


int get_iterations(vec2 offset) {
    float real = lim_pos[0] + offset[0];
    float imag = lim_pos[1] + offset[1];

    int iterations = 0;
    float const_real = real;
    float const_imag = imag;

    while (iterations < iterations_max) {

        float tmp_real = real;
        real = (real * real - imag * imag) + const_real;
        imag = (2.0 * tmp_real * imag) + const_imag;

        float dist = real * real + imag * imag;

        if (dist > 4.0)
        break;
        ++iterations;
    }
    return iterations;
}

vec4 return_color(vec2 offset) {
    int iter = get_iterations(offset);

    if (iter == iterations_max) {
        gl_FragDepth = 0.0f;
        return vec4(0.0f, 0.0f, 0.0f, 1.0f);
    }

    float iterations = float(iter) / iterations_max;
    return vec4(0.0f, iterations, 0.0f, 1.0f);
}

void main() {
    if (bPos.x < clip_bounds.x || bPos.x > clip_bounds.z || bPos.y < clip_bounds.y || bPos.y > clip_bounds.w){
        //discard;
    }
    vec4 cumulative_col = vec4(0.0, 0.0, 0.0, 0.0);
    for (int y = 0; y < supersample; ++y){
        for (int x = 0; x < supersample; ++x){
            vec2 offset = vec2(float(x) / supersample, float(y) / supersample);

            offset = (offset) / vec2(screen_x, screen_y);// * (2 / vec2(screen_x, screen_y));

            cumulative_col += return_color(offset);
        }
    }
    cumulative_col = cumulative_col / (supersample * supersample);

    frag_color = cumulative_col;
}