#version 330


const int STR_LENGTH = 10;

layout(points) in;
layout(triangle_strip, max_vertices = 40) out;

uniform vec2 glyph_size;
uniform bool vertical;
uniform float glyph_step;
uniform int start_number;
uniform int delta_number;

in int vertex_index[];

flat out int glyph_id;
out vec2 uv;

void main(void)
{
    vec4 p = gl_in[0].gl_Position;

    ////////////////////////////////////////////////////////////////
    // build string

    int str[STR_LENGTH];
    int cur_idx = 0;
    int number = (vertex_index[0] * delta_number) + start_number;
    bool neg = number < 0;

    if (number < 0)
        number = -number;

    if ((delta_number % 1000) == 0) {
        number /= 1000;
        str[cur_idx++] = 75; // k
    }

    do {
        int digit = number % 10;
        str[cur_idx++] = 16 + digit;
        number /= 10;
    } while (number != 0 || cur_idx == (STR_LENGTH-1));

    if (neg)
        str[cur_idx++] = 13;


    ////////////////////////////////////////////////////////////////
    // generate glyphs

    if (vertical) {
        int offset = 0;
        for (int idx = cur_idx-1; idx >= 0; idx--) {
            gl_Position = p + vec4(vec2(0, offset) * glyph_size, 0.0, 0.0);
            uv = vec2(0., 0.);
            glyph_id = str[idx];
            EmitVertex();

            gl_Position = p + vec4(vec2(1, offset) * glyph_size, 0.0, 0.0);
            uv = vec2(0., 1.);
            glyph_id = str[idx];
            EmitVertex();

            gl_Position = p + vec4(vec2(0, offset + 1) * glyph_size, 0.0, 0.0);
            uv = vec2(1., 0.);
            glyph_id = str[idx];
            EmitVertex();

            gl_Position = p + vec4(vec2(1, offset + 1) * glyph_size, 0.0, 0.0);
            uv = vec2(1., 1.);
            glyph_id = str[idx];
            EmitVertex();

            EndPrimitive();

            offset += 1;
        }
    } else {
        int offset = 0;
        for (int idx = cur_idx-1; idx >= 0; idx--) {
            gl_Position = p + vec4(vec2(offset, 0.0) * glyph_size, 0.0, 0.0);
            uv = vec2(0., 0.);
            glyph_id = str[idx];
            EmitVertex();

            gl_Position = p + vec4(vec2(offset + 1, 0.0) * glyph_size, 0.0, 0.0);
            uv = vec2(1., 0.);
            glyph_id = str[idx];
            EmitVertex();

            gl_Position = p + vec4(vec2(offset, -1) * glyph_size, 0.0, 0.0);
            uv = vec2(0., 1.);
            glyph_id = str[idx];
            EmitVertex();

            gl_Position = p + vec4(vec2(offset + 1, -1) * glyph_size, 0.0, 0.0);
            uv = vec2(1., 1.);
            glyph_id = str[idx];
            EmitVertex();

            EndPrimitive();

            offset += 1;
        }
    }
}