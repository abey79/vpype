#version 330

uniform float ruler_width;
uniform float ruler_height;
uniform mat4 projection;

in vec2 in_vert;

void main() {
    gl_Position = vec4(in_vert, 0.0, 1.0);

    if (gl_Position.x == 0.0) {
        gl_Position.x = -1.0 + ruler_width;
    }

    if (gl_Position.y == 0.0) {
        gl_Position.y = 1.0 - ruler_height;
    }
}
