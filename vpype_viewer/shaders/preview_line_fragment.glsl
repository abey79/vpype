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

vec4 stroke(float distance, float linewidth, float antialias, vec4 color)
{
    vec4 frag_color;
    float t = linewidth/2.0 - antialias;
    float signed_distance = distance;
    float border_distance = abs(signed_distance) - t;
    float alpha = border_distance/antialias;

    alpha = exp(-alpha*alpha);

    if (border_distance > (linewidth/2.0 + antialias))
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

vec4 cap(int type, float dx, float dy, float linewidth, float antialias, vec4 color)
{
    float d = 0.0;
    dx = abs(dx);
    dy = abs(dy);
    float t = linewidth/2.0 - antialias;

    if (type == 0)  // None
        discard;
    else if (type == 1) // Round
        d = sqrt(dx*dx+dy*dy);
    else if (type == 3) // Triangle in
        d = (dx+abs(dy));
    else if (type == 2) // Triangle out
        d = max(abs(dy), (t+dx-abs(dy)));
    else if (type == 4) // Square
        d = max(dx, dy);
    else if (type == 5) // Butt
        d = max(dx+t, dy);

    return stroke(d, linewidth, antialias, color);
}

uniform vec4  color;
uniform float antialias;
uniform float linewidth;

uniform bool kill_frag_shader;
uniform bool debug_v_caps;

in float v_length;
in vec2  v_texcoord;

out vec4 fragColor;

void main()
{
    float distance = v_texcoord.y;

    if (debug_v_caps)
    {
        if (v_texcoord.x < 0.0) {
            distance = length(v_texcoord);
        } else if (v_texcoord.x > v_length) {
            distance = length(v_texcoord - vec2(v_length, 0.0));
        }

        //fragColor.rgb = vec3(10. * v_caps.y / 255., 0., 0.);
        float val = distance / (antialias + linewidth/2.);
        fragColor.rgb = vec3(val, 0, -val);
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

    fragColor = stroke(distance, linewidth, antialias, color);
}
