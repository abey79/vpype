.. _api:

===========
Plug-in API
===========

.. module:: vpype

Collections
===========

.. autoclass:: LineCollection
   :members:

.. autoclass:: VectorData
   :members:

Command decorators
==================

.. autodecorator:: generator

.. autodecorator:: layer_processor

.. autodecorator:: global_processor

.. autodecorator:: block_processor

.. autodecorator:: pass_state


File I/O
========

.. autofunction:: read_svg

.. autofunction:: read_multilayer_svg

.. autofunction:: write_svg


Primitives
==========

.. autofunction:: line

.. autofunction:: rect

.. autofunction:: arc

.. autofunction:: circle

.. autofunction:: ellipse


Geometry
========

.. autofunction:: interpolate

.. autofunction:: crop_half_plane

.. autofunction:: crop

.. autofunction:: reloop


Unit management
===============

.. autoclass:: LengthType
   :members:

.. autofunction:: convert_length

.. autofunction:: convert_page_format

Layer management
================

.. autoclass:: LayerType
   :members:

.. autofunction:: single_to_layer_id

.. autofunction:: multiple_to_layer_ids

.. autoclass:: VpypeState
   :members:


Misc
====

.. autoclass:: LineIndex
   :members:

.. autoclass:: PageSizeType
   :members:

.. autofunction:: as_vector
