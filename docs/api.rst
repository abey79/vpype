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


File I/O
========

.. autofunction:: read_svg

.. autofunction:: read_multilayer_svg


Unit management
===============

.. autoclass:: LengthType
   :members:

.. autofunction:: convert

Layer management
================

.. autoclass:: LayerType
   :members:

.. autofunction:: single_to_layer_id

.. autofunction:: multiple_to_layer_ids

.. autoclass:: VpypeState
   :members:

.. autodecorator:: pass_state


Misc
====

.. autoclass:: LineIndex
   :members:

.. autoclass:: PageSizeType
   :members:

.. autofunction:: as_vector

.. autofunction:: interpolate_line
