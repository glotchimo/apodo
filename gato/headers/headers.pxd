"""
gato.headers.headers.pxd
~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the Cython build of the custom Headers class.
"""

# cython: language_level=3, boundscheck=False, wraparound=False, annotation_typing=False
import cython

@cython.freelist(1024)
cdef class Headers:

    cdef dict values
    cdef list raw
    cdef bint evaluated

    cpdef get(self, str key, object default=*)
    cpdef eval(self)
    cpdef dump(self)

    cdef dict parse_cookies(self)
