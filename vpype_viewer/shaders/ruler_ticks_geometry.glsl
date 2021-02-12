#version 330

#define TICK_DIMMING 0.2

layout(points) in;
layout(line_strip, max_vertices = 32) out;

uniform float viewport_dim;
uniform float document_dim;
uniform float ruler_thickness;
uniform bool vertical;
uniform int divisions[3];
uniform float offset;
uniform float scale;
uniform int start_number;
uniform int delta_number;

in int vertex_index[];

out float dimming;

void main(void)
{
    vec4 p = gl_in[0].gl_Position;


    // emit the major tick
    float base_number = (vertex_index[0] * delta_number) + start_number;
    float major_tick_dimming = 1.0;
    if (base_number < 0 || base_number > document_dim)
        major_tick_dimming = TICK_DIMMING;

    gl_Position = p;
    dimming = major_tick_dimming;
    EmitVertex();
    if (vertical)
        gl_Position = p + vec4(ruler_thickness, 0.0, 0.0, 0.0);
    else
        gl_Position = p + vec4(0.0, -ruler_thickness, 0.0, 0.0);
    dimming = major_tick_dimming;
    EmitVertex();
    EndPrimitive();

    // emit the divisions ticks
    for (int i = 1; i < divisions[0]; i++ ) {
        float delta = i * scale / divisions[0] * 2. / viewport_dim;
        float tick_width = 0.1 * ruler_thickness;
        if ((i % divisions[1]) == 0)
            tick_width = 0.4 * ruler_thickness;
        else if ((i % divisions[2]) == 0)
            tick_width = 0.2 * ruler_thickness;

        float tick_dimming = 1.0;
        float number = base_number + i * delta_number / divisions[0];
        if (number < 0 || number > document_dim)
            tick_dimming = TICK_DIMMING;

        if (vertical) {
            gl_Position = p + vec4(ruler_thickness - tick_width, -delta, 0.0, 0.0);
            dimming = tick_dimming;
            EmitVertex();
            gl_Position = p + vec4(ruler_thickness, -delta, 0.0, 0.0);
            dimming = tick_dimming;
            EmitVertex();
        } else {
            gl_Position = p + vec4(delta, -ruler_thickness + tick_width, 0.0, 0.0);
            dimming = tick_dimming;
            EmitVertex();
            gl_Position = p + vec4(delta, -ruler_thickness, 0.0, 0.0);
            dimming = tick_dimming;
            EmitVertex();
        }

        EndPrimitive();
    }
}