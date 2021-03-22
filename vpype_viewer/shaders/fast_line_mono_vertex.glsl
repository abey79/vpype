#version 330

// single color basic 2D vertex shader

uniform mat4 projection;

in vec2 in_vert;

void main() {
    gl_Position = projection * vec4(in_vert, 0.0, 1.0);
}
