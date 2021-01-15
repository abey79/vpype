#version 330

uniform mat4 projection;

in vec2 in_vert;
in vec4 in_color;

out vec4 v_color;

void main() {
    v_color = in_color;
    gl_Position = projection * vec4(in_vert, 0.0, 1.0);
}
