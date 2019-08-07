"""
gato.multipart.containers
~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements some multipart-specific custom container classes.
"""

import os
import uuid
import inspect
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
    """ Implements the `MultipartEncoder` utility class.

    :param `delimiter`: A `bytes` representation of a `delimiter`.
    :param `params`: A `dict` of parameters.
    :param `chunk_size`: The int size of the given chunk.
    :param `loop`: An async value `loop` to run through.
    :param `encoding`: A `str` encoding, default being `utf-8`.
    """

    def __init__(
        self,
        delimiter,
        params,
        chunk_size=1 * 1024 * 1024,
        loop=None,
        encoding="utf-8",
    ):
        self.delimiter = b"--" + delimiter
        self.params = params
        self.chunk_size = chunk_size
        self.evaluated = False
        self.loop = loop
        self.encoding = encoding

    def __iter__(self):
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

    def create_headers(self, name, value):
        """ Creates a serialized set of multipart headers.

        :param `name`: The `str` name of the file.
        :param `value`: An object with file data.

        :return: A `str` representation of the headers.
        """
        headers = {"Content-Dispositon": "form-data", "name": name}

        if type(value) is FileUpload:
            headers["filename"] = value.name

        return str(headers).encode(self.encoding)

    def stream_value(self, value):
        """ Yields a stream of the file value.

        :param `value`: An object with file data.

        :return: A yielded stream of file data.
        """
        if type(value) is FileUpload:
            while True:
                chunk = (
                    self.loop.run_until_complete(value.f.read(self.chunk_size))
                    if value.is_async
                    else value.f.read(self.chunk_size)
                )

                size = len(chunk)
                if size:
                    yield chunk
                else:
                    break

        else:
            if type(value) is int:
                yield str(value).encode()
            elif type(value) is str:
                yield value.encode(self.encoding)
            else:
                yield value
