#version 330

uniform vec4 color;

in float dimming;

out vec4 f_color;

void main() {
    f_color = color;
    f_color.a *= dimming;
}
