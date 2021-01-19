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
layout(triangle_strip, max_vertices = 4) out;// Outputs a triangle strip with 4 vertices

uniform mat4 projection;
uniform float antialias;
uniform float linewidth;

out float v_length;
out vec2 v_texcoord;

float compute_u(vec2 p0, vec2 p1, vec2 p)
{
    // Projection p' of p such that p' = p0 + u*(p1-p0)
    // Then  u *= length(p1-p0)
    vec2 v = p1 - p0;
    float l = length(v);

    return ((p.x-p0.x)*v.x + (p.y-p0.y)*v.y) / l;
}

float line_distance(vec2 p0, vec2 p1, vec2 p)
{
    // Projection p' of p such that p' = p0 + u*(p1-p0)
    vec2 v = p1 - p0;
    float l2 = v.x*v.x + v.y*v.y;
    float u = ((p.x-p0.x)*v.x + (p.y-p0.y)*v.y) / l2;

    // h is the projection of p on (p0,p1)
    vec2 h = p0 + u*v;

    return length(p-h);
}

void main(void)
{
    // Get the four vertices passed to the shader
    vec2 p0 = gl_in[0].gl_Position.xy;// start of previous segment
    vec2 p1 = gl_in[1].gl_Position.xy;// end of previous segment, start of current segment
    vec2 p2 = gl_in[2].gl_Position.xy;// end of current segment, start of next segment
    vec2 p3 = gl_in[3].gl_Position.xy;// end of next segment

    // Determine the direction of each of the 3 segments (previous, current, next)
    vec2 v0 = normalize(p1 - p0);
    vec2 v1 = normalize(p2 - p1);
    vec2 v2 = normalize(p3 - p2);

    // Determine the normal of each of the 3 segments (previous, current, next)
    vec2 n0 = vec2(-v0.y, v0.x);
    vec2 n1 = vec2(-v1.y, v1.x);
    vec2 n2 = vec2(-v2.y, v2.x);

    // Determine miter lines by averaging the normals of the 2 segments
    vec2 miter_a = normalize(n0 + n1);// miter at start of current segment
    vec2 miter_b = normalize(n1 + n2);// miter at end of current segment

    // Determine the length of the miter by projecting it onto normal
    vec2 p, v;
    float d;
    float w = linewidth/2.0 + antialias;
    v_length = length(p2-p1);
    float length_a = w / dot(miter_a, n1);
    float length_b = w / dot(miter_b, n1);

    // Angle between prev and current segment (sign only)
    float d0 = -sign(v0.x*v1.y - v0.y*v1.x);

    // Angle between current and next segment (sign only)
    float d1 = -sign(v1.x*v2.y - v1.y*v2.x);

    // model to texcoord transformation matrix to convert
    // points to texcoords
    mat2 texcoord_matrix = mat2(v1.x, n1.x, v1.y, n1.y);

    // Generate the triangle strip
    // First vertex
    // ------------------------------------------------------------------------
    // Cap at start
    if (p0 == p1) {
        p = p1 - w*v1 + w*n1;
    } else {
        p = p1 + length_a * miter_a;
    }

    v_texcoord = texcoord_matrix * (p - p1);
    gl_Position = projection * vec4(p, 0.0, 1.0);
    EmitVertex();

    // Second vertex
    // ------------------------------------------------------------------------
    // Cap at start
    if (p0 == p1) {
        p = p1 - w*v1 - w*n1;
    } else {
        p = p1 - length_a * miter_a;
    }

    v_texcoord = texcoord_matrix * (p - p1);
    gl_Position = projection * vec4(p, 0.0, 1.0);
    EmitVertex();

    // Third vertex
    // ------------------------------------------------------------------------
    // Cap at end
    if (p2 == p3) {
        p = p2 + w*v1 + w*n1;
        // Regular join
    } else {
        p = p2 + length_b * miter_b;
    }

    v_texcoord = texcoord_matrix * (p - p1);
    gl_Position = projection * vec4(p, 0.0, 1.0);
    EmitVertex();

    // Fourth vertex
    // ------------------------------------------------------------------------
    // Cap at end
    if (p2 == p3) {
        p = p2 + w*v1 - w*n1;
    } else {
        p = p2 - length_b * miter_b;
    }

    v_texcoord = texcoord_matrix * (p - p1);
    gl_Position = projection * vec4(p, 0.0, 1.0);
    EmitVertex();

    EndPrimitive();
}
