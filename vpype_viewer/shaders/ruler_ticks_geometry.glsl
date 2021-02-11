#version 330

layout(points) in;
layout(line_strip, max_vertices = 32) out;

uniform float viewport_dim;
uniform float ruler_thickness;
uniform bool vertical;
uniform int divisions[3];
uniform float offset;
uniform float scale;

void main(void)
{
    vec4 p = gl_in[0].gl_Position;

    if (vertical)
    {
        gl_Position = p;
        EmitVertex();

        gl_Position = p + vec4(ruler_thickness, 0.0, 0.0, 0.0);
        EmitVertex();

        EndPrimitive();

        for (int i = 1; i < divisions[0]; i++ ) {
            float delta = i * scale / divisions[0] * 2. / viewport_dim;
            float tick_width = 0.2 * ruler_thickness;
            if ((i % divisions[1]) == 0)
                tick_width = 0.6 * ruler_thickness;
            else if ((i % divisions[2]) == 0)
                tick_width = 0.4 * ruler_thickness;


            gl_Position = p + vec4(ruler_thickness - tick_width, -delta, 0.0, 0.0);
            EmitVertex();

            gl_Position = p + vec4(ruler_thickness, -delta, 0.0, 0.0);
            EmitVertex();

            EndPrimitive();
        }
    }
    else
    {
        gl_Position = p;
        EmitVertex();

        gl_Position = p + vec4(0.0, -ruler_thickness, 0.0, 0.0);
        EmitVertex();

        EndPrimitive();

        for (int i = 1; i < divisions[0]; i++ ) {
            float delta = i * scale / divisions[0] * 2. / viewport_dim;
            float tick_width = 0.2 * ruler_thickness;
            if ((i % divisions[1]) == 0)
                tick_width = 0.6 * ruler_thickness;
            else if ((i % divisions[2]) == 0)
                tick_width = 0.4 * ruler_thickness;


            gl_Position = p + vec4(delta, -ruler_thickness + tick_width, 0.0, 0.0);
            EmitVertex();

            gl_Position = p + vec4(delta, -ruler_thickness, 0.0, 0.0);
            EmitVertex();

            EndPrimitive();
        }
    }
}