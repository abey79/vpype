#version 330

uniform float viewport_dim;
uniform bool vertical;
uniform float offset;
uniform float scale;

in float position;

out int vertex_index;

void main()
{
    vertex_index = gl_VertexID;
    if (vertical) {
        gl_Position = vec4(-1.0, 1.0 - 2 * (gl_VertexID * scale - offset)  / viewport_dim, 0.0, 1.0);
    } else {
        gl_Position = vec4(-1.0 + 2 * (gl_VertexID * scale - offset) / viewport_dim, 1.0, 0.0, 1.0);
    }

    gl_PointSize = 5.0;
}
