"""
gato.multipart.containers
~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements some multipart-specific custom container classes.
"""

import inspect
import uuid
import os
from io import BytesIO


class BufferedIterable:
    """ Implements a custom buffered iterable object. """

    def __init__(self, item):
        self.item = item
        self.cursor = self.item.__iter__()
        self.buffer = bytearray()

    def read(self, size):
        while len(self.buffer) < size:
            self.buffer.extend(self.cursor.__next__())

        temp = self.buffer[: size + 1]
        self.buffer = self.buffer[size + 1 :]

        return temp


class FileUpload:
    """ Implements a file to be uploaded.

    The `__init__` method of this class checks for the presence of
    `file`, `path`, `content`, and `iterable`, and builds `self.file` depending
    on which is supplied, in the order of the writen conditional.

    :param `name`: The str `name` of the file.
    :param `path`: (optional) The str `path` of the file.
    :param `content`: (optional) A bytes-like object representing the contents of the file.
    :param `iterable`: (optional) An `iterable` object representing the file.
    :param `file`: (optional) A `file` object.
    :param `headers`: (optional) A `list` of file `headers`.
    """

    def __init__(
        self,
        name,
        path=None,
        content=None,
        iterable=None,
        file=None,
        headers=None,
    ):
        self.name = name or str(uuid.uuid4())
        self.headers = headers

        if file:
            self.file = file
        elif path:
            self.file = open(path, "rb")
            if not self.name:
                self.name = os.path.basename(path)
        elif content:
            self.file = BytesIO(initial_bytes=content)
        elif iterable:
            self.file = BufferedIterable(iterable)
        else:
            raise Exception(
                "You must supply one of these: path, content, iterable, or file"
            )

        self.is_async = inspect.iscoroutine(self.file.read)


class MultipartEncoder:
    def __init__(
        self,
        delimiter: bytes,
        params: dict,
        chunk_size: int = 1 * 1024 * 1024,
        loop=None,
        encoding: str = "utf-8",
    ):
        self.delimiter = b"--" + delimiter
        self.params = params
        self.chunk_size = chunk_size
        self.evaluated = False
        self.loop = loop
        self.encoding = encoding

    def create_headers(self, name: str, value) -> bytes:
        """

        :param name:
        :param value:
        :return:
        """
        if isinstance(value, FileUpload):
            return f'Content-Disposition: form-data; name="{name}"; filename="{value.name}"'.encode(
                self.encoding
            )
        else:
            return f'Content-Disposition: form-data; name="{name}"'.encode(
                self.encoding
            )

    def stream_value(self, value) -> bytes:
        """

        :param value:
        :return:
        """
        if isinstance(value, FileUpload):
            while True:
                if value.is_async:
                    chunk = self.loop.run_until_complete(
                        value.f.read(self.chunk_size)
                    )
                else:
                    chunk = value.f.read(self.chunk_size)
                size = len(chunk)
                if size == 0:
                    break
                yield chunk
        else:
            if isinstance(value, int):
                yield str(value).encode()
            elif isinstance(value, str):
                yield value.encode(self.encoding)
            else:
                yield value

    def __iter__(self):
        """

        :return:
        """
        if self.evaluated:
            raise Exception("Streaming encoder cannot be evaluated twice.")
        for name, value in self.params.items():
            header = (
                self.delimiter
                + b"\r\n"
                + self.create_headers(name, value)
                + b"\r\n\r\n"
            )
            yield header
            for chunk in self.stream_value(value):
                yield chunk
            yield b"\r\n"
        yield self.delimiter + b"--"
        self.evaluated = True
