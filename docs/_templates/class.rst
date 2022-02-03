{{ fullname | replace("vpype.", "") | escape | underline }}

{% set classes = members | reject("in", methods) | reject("in", attributes) | reject("ge", "_") | list %}

.. currentmodule:: {{ module }}

.. autoclass:: {{ fullname }}

   {% block classes %}
   {% if classes %}
   .. rubric:: Classes

   .. autosummary::
      :toctree:
      :nosignatures:
      :template: class.rst
   {% for item in classes %}
      ~{{ fullname }}.{{ item }}
   {%- endfor %}
   {%- endif %}
   {% endblock %}

   {% block methods %}
   {% if methods %}
   .. rubric:: Methods

   .. autosummary::
      :nosignatures:
   {% for item in methods %}
    {%- if item not in inherited_members %}
      ~{{ fullname }}.{{ item }}
    {%- endif %}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block attributes %}
   {% if attributes|length > 0 %}
   .. rubric:: Attributes

   .. autosummary::
   {% for item in attributes %}
    {%- if item not in inherited_members %}
      ~{{ fullname }}.{{ item }}
    {%- endif %}
   {%- endfor %}
   {% endif %}
   {% endblock %}

{% block methods_detail %}
{% if methods %}

Methods
-------

{% for item in methods %}
{%- if item not in inherited_members %}

.. automethod:: {{ module }}.{{ objname }}.{{ item }}

{%- endif %}
{%- endfor %}
{% endif %}
{% endblock %}

{% block attributes_detail %}
{% if attributes %}

Attributes
----------

{% for item in attributes %}
{%- if item not in inherited_members %}

.. autoattribute:: {{ module }}.{{ objname }}.{{ item }}
{%- endif %}

{%- endfor %}
{% endif %}
{% endblock %}