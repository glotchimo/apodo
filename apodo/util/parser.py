"""
apodo.util.parser
~~~~~~~~~~~~~~~~~

This module contains the `Parser` class.
"""

from apodo.net.connection import Connection


class Parser:
    """ Implements the `Parser` class.
    
    This class serves as a functional default HTTP parser for the `Connection`
    object, but is not optimised or C-powered. The intention is that other parsers,
    namely Kolla, will be used in its place when completed.

    :param connection: A `Connection` instance.
    """

    def __init__(self, connection: Connection):
        self.connection: Connection = connection

    def parse(self, data):
        """ Parses request data. """
        self.request, *headers, _, self.body = data.split("\r\n")
        self.method, self.path, self.protocol = self.request.split(" ")
        self.headers = dict(line.split(":", maxsplit=1) for line in headers)

        return {
            "method": self.method,
            "path": self.path,
            "protocol": self.protocol,
            "headers": self.headers,
            "body": self.body,
        }
