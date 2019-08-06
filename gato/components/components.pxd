"""
gato.components.components.pxd
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
This module implements the Cython build of the ComponentsEngine class.
"""

cdef class ComponentsEngine:

    cdef dict index
    cdef dict ephemeral_index
    cdef object request_class
    cdef void reset(self)

    cpdef ComponentsEngine clone(self)
