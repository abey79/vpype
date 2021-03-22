#version 330

/*
This example is a port to ModernGL of code by Nicolas P. Rougier from his "Python & OpenGL
for Scientific Visualization" free online book. Available under the (new) BSD License.

Book is available here:
https://github.com/rougier/python-opengl

Background information on this code:
https://github.com/rougier/python-opengl/blob/master/09-lines.rst

Original code on which this example is based:
https://github.com/rougier/python-opengl/blob/master/code/chapter-09/geom-path.py
*/


layout(lines_adjacency) in;// 4 points at the time from vertex shader
layout(triangle_strip, max_vertices = 6) out;// Outputs a triangle strip with 4 vertices

uniform mat4 projection;
uniform float antialias;
uniform float pen_width;

out float v_length;
out vec2 v_texcoord;

void emit_vertex(vec2 p, vec2 p1, mat2 texcoord_matrix, mat4 projection)
{
    v_texcoord = texcoord_matrix * (p - p1);
    gl_Position = projection * vec4(p, 0.0, 1.0);
    EmitVertex();
}


void main(void)
{
    float w = pen_width/2.0 + antialias;

    // Get the four vertices passed to the shader
    vec2 p0 = gl_in[0].gl_Position.xy;// start of previous segment
    vec2 p1 = gl_in[1].gl_Position.xy;// end of previous segment, start of current segment
    vec2 p2 = gl_in[2].gl_Position.xy;// end of current segment, start of next segment
    vec2 p3 = gl_in[3].gl_Position.xy;// end of next segment

    // Determine the direction of each of the 3 segments (previous, current, next)
    vec2 v0 = normalize(p1 - p0);
    vec2 v1 = normalize(p2 - p1);
    vec2 v2 = normalize(p3 - p2);

    float v0v1 = dot(v0, v1);
    float v1v2 = dot(v1, v2);

    float d1 = sign(v0.x * v1.y - v0.y * v1.x);// change of direction of this segment: pos means CW
    float d2 = sign(v1.x * v2.y - v1.y * v2.x);// change of direction of next segment: pos means CW

    // Determine the normal of each of the 3 segments (previous, current, next)
    vec2 n0 = vec2(-v0.y, v0.x);
    vec2 n1 = vec2(-v1.y, v1.x);
    vec2 n2 = vec2(-v2.y, v2.x);

    v_length = length(p2 - p1);
    float critical_length_mid = length(p2 - p1 + w * (n1 + v1));
    float critical_length_a = min(length(p1 - p0 + w * (n0 + v0)), critical_length_mid);
    float critical_length_b = min(length(p3 - p2 + w * (n2 + v2)), critical_length_mid);

    // Determine miter lines by averaging the normals of the 2 segments
    vec2 miter_a = normalize(n0 + n1);
    vec2 miter_b = normalize(n1 + n2);
    float length_a = w / dot(miter_a, n1);
    float length_b = w / dot(miter_b, n1);

    // model to texcoord transformation matrix to convert
    // points to texcoords
    mat2 texcoord_matrix = mat2(v1.x, n1.x, v1.y, n1.y);

    vec2 p;

    /////////////// SEGMENT START ///////////////////
    if (p0 == p1 || length_a >= critical_length_a) {
        p = p1 + w * (-v1 + n1);
        emit_vertex(p, p1, texcoord_matrix, projection);

        p = p1 + w * (-v1 - n1);
        emit_vertex(p, p1, texcoord_matrix, projection);
    } else if (v0v1 >= 0) {
        p = p1 + length_a * miter_a;
        emit_vertex(p, p1, texcoord_matrix, projection);

        p = p1 - length_a * miter_a;
        emit_vertex(p, p1, texcoord_matrix, projection);
    } else {
        p = p1 + w * 0.5 * (-v1 - d1 * n1 + v0 - d1 * n0);
        emit_vertex(p, p1, texcoord_matrix, projection);

        if (d1 == -1) {
            p = p1 + w * (-v1 - d1 * n1);
            emit_vertex(p, p1, texcoord_matrix, projection);

            p = p1 + d1 * length_a * miter_a;
            emit_vertex(p, p1, texcoord_matrix, projection);
        } else {
            p = p1 + d1 * length_a * miter_a;
            emit_vertex(p, p1, texcoord_matrix, projection);

            p = p1 + w * (-v1 - d1 * n1);
            emit_vertex(p, p1, texcoord_matrix, projection);
        }
    }

    /////////////// SEGMENT END ///////////////////
    if (p2 == p3 || length_b >= critical_length_b) {
        p = p2 + w * (v1 + n1);
        emit_vertex(p, p1, texcoord_matrix, projection);

        p = p2 + w * (v1 - n1);
        emit_vertex(p, p1, texcoord_matrix, projection);
    } else if (v1v2 >= 0) {
        p = p2 + length_b * miter_b;
        emit_vertex(p, p1, texcoord_matrix, projection);

        p = p2 - length_b * miter_b;
        emit_vertex(p, p1, texcoord_matrix, projection);
    } else {

        if (d2 == -1) {
            p = p2 + w * (v1 - d2 * n1);
            emit_vertex(p, p1, texcoord_matrix, projection);

            p = p2 + d2 * length_b * miter_b;
            emit_vertex(p, p1, texcoord_matrix, projection);
        } else {
            p = p2 + d2 * length_b * miter_b;
            emit_vertex(p, p1, texcoord_matrix, projection);

            p = p2 + w * (v1 - d2 * n1);
            emit_vertex(p, p1, texcoord_matrix, projection);
        }

        p = p2 + w * 0.5 * (v1 - d2 * n1 - v2 - d2 * n2);
        emit_vertex(p, p1, texcoord_matrix, projection);
    }

    EndPrimitive();
}