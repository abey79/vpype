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

vec4 stroke(float distance, float pen_width, float antialias, vec4 color)
{
    vec4 frag_color;
    float t = pen_width/2.0 - antialias;
    float signed_distance = distance;
    float border_distance = abs(signed_distance) - t;
    float alpha = border_distance/antialias;

    alpha = exp(-alpha*alpha);

    if (border_distance > (pen_width/2.0 + antialias))
    {
        discard;
    }
    else if (border_distance < 0.0)
    {
        frag_color = color;
    }
    else
    {
        frag_color = vec4(color.rgb, color.a * alpha);
    }

    return frag_color;
}

uniform vec4  color;
uniform float antialias;
uniform float pen_width;

uniform bool kill_frag_shader;
uniform bool debug_view;

in float v_length;
in vec2  v_texcoord;

out vec4 fragColor;

void main()
{
    float distance = v_texcoord.y;

    if (debug_view)
    {
        if (v_texcoord.x < 0.0) {
            distance = length(v_texcoord);
        } else if (v_texcoord.x > v_length) {
            distance = length(v_texcoord - vec2(v_length, 0.0));
        }

        //fragColor.rgb = vec3(10. * v_caps.y / 255., 0., 0.);
        float w = antialias + pen_width/2.;
        float val = distance / w;
        float y_val = (v_texcoord.x + w) / (v_length + 2*w);
        fragColor.rgb = vec3(abs(val), 0, y_val);
        fragColor.a = 1.0;
        return;
    }

    if (kill_frag_shader)
    {
        fragColor = color;
        return;
    }

    if (v_texcoord.x < 0.0) {
        distance = length(v_texcoord);
    } else if (v_texcoord.x > v_length) {
        distance = length(v_texcoord - vec2(v_length, 0.0));
    }

    fragColor = stroke(distance, pen_width, antialias, color);
}
