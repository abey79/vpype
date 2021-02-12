#version 330

uniform vec2 position;
uniform vec2 glyph_size;

in int char;

out int v_char;

void main()
{
    gl_Position = vec4(position, 0., 1.);
    gl_Position.x += glyph_size.x * gl_VertexID;
    v_char = char;
}
