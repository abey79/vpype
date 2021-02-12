#version 330

layout(points) in;
layout(triangle_strip, max_vertices = 4) out;

uniform vec2 glyph_size;

in int v_char[];

flat out int glyph_id;
out vec2 uv;

void main(void)
{
    int char = v_char[0];
    int glyph;
    if (char >= 32 && char <= 126)
        glyph = char - 32;
    else if (char >= 161 && char <= 255)
        glyph = 95 + char - 161;
    else
        return;

    // top-left char position
    vec4 p = gl_in[0].gl_Position;

    // generate quad
    gl_Position = p;
    uv = vec2(0., 0.);
    glyph_id = glyph;
    EmitVertex();

    gl_Position = p + vec4(glyph_size.x, 0.0, 0.0, 0.0);
    uv = vec2(1., 0.);
    glyph_id = glyph;
    EmitVertex();

    gl_Position = p + vec4(0.0, -glyph_size.y, 0.0, 0.0);
    uv = vec2(0., 1.);
    glyph_id = glyph;
    EmitVertex();

    gl_Position = p + vec4(glyph_size.x, -glyph_size.y, 0.0, 0.0);
    uv = vec2(1., 1.);
    glyph_id = glyph;
    EmitVertex();

    EndPrimitive();
}