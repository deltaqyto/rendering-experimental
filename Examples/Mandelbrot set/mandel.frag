#version 330 core


in vec2 tpos;
out vec4 frag_color;

uniform int iterations_max;


int get_iterations() {
    float real = tpos[0] * 1.8 - 0.8;
    float imag = tpos[1] * 1.4;

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

vec4 return_color() {
    int iter = get_iterations();

    if (iter == iterations_max) {
        gl_FragDepth = 0.0f;
        return vec4(0.0f, 0.0f, 0.0f, 1.0f);
    }

    float iterations = float(iter) / iterations_max;
    return vec4(0.0f, iterations, 0.0f, 1.0f);
}

void main() {
    frag_color = return_color();
}