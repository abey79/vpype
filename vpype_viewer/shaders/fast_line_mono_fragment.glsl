#version 330

// single color basic 2D vertex shader

uniform vec4 color;

out vec4 f_color;

void main() {
    f_color = color;
}
