#version 330

uniform mat4 projection;
uniform vec4 colors[7];

in vec2 in_vert;
in int color_idx;

flat out vec4 v_color;

void main() {
    v_color = colors[color_idx];
    if ((gl_VertexID % 2) == 0)
        v_color.rgb *= 0.6;

    gl_PointSize = 5.0;
    gl_Position = projection * vec4(in_vert, 0.0, 1.0);
}
