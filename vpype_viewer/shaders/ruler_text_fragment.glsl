#version 330

uniform vec4 color;
uniform sampler2DArray glyphs;

flat in int glyph_id;
in vec2 uv;
in float dimming;

out vec4 f_color;

void main() {
    f_color = color * texture(glyphs, vec3(uv, glyph_id));
    f_color.a *= dimming;
}
