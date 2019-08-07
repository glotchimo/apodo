"""
gato.multipart.parser.pyx
~~~~~~~~~~~~~~~~~~~~~~~~~

This module implements the Cython builds of all multipart
utility methods and classes.
"""

import os
import uuid
import shutil
from tempfile import gettempdir


DEF EXPECTING_BOUNDARY = 1
DEF EXPECTING_CONTENT_HEADERS = 2
DEF EXPECTING_BUFFER = 3


cdef class UploadedFile:
    """ Implements the `UploadedFile` class.

    This class serves as an interface for uploaded files.
    This is an abstract class.

    :param `filename`: (optional) The name of the given file.
    """

    cdef public str filename

    def __init__(self, filename=None):
        self.filename = filename

    async def save(self, str destination):
        raise NotImplementedError

    async def read(self, int count=0):
        raise NotImplementedError

    async def write(self, data: bytes):
        raise NotImplementedError

    def seek(self, pos):
        raise NotImplementedError


cdef class MemoryFile(UploadedFile):
    """ Implements the `MemoryFile` class.

    This class is used when it is effective to store
    file data in memory, before it is offloaded to the disk.

    :param `filename`: (optional) The name of the given file.
    :param `file`: (optional) A file object.
    """

    cdef:
        bytearray f
        int pointer

    def __init__(self, filename=None, file=None):
        super().__init__(filename=filename)

        self.file = file or bytearray()
        self.pointer = 0

    def seek(self, position):
        """ Sets `self.pointer` to a given position.

        :param position: An `int` position.
=       """
        self.pointer = position

    async def write(self, data):
        """ Writes byte data to the `file`.

        This method uses the `extend` utility to add `data` to
        `self.file`, then updates `self.pointer` according to the size
        of `data`.

        :param `data`: A `bytes`-like set of `data`.
        """
        self.file.extend(data)
        self.pointer += len(data)

    async def read(self, count=0):
        """ Reads and returns `file` contents.

        :param `count`: A `count` of characters to read.
        """
        if count:
            data = self.file[self.pointer:(self.pointer + count)]
            self.pointer += count
        else:
            data = self.file[self.pointer:]
            self.pointer = len(self.file)

        return bytes(data)

    async def save(self, destination):
        """ Saves `self.file` to the given `destination`.

        :param `destination`: A `str` path to the desired save destination.
        """
        with open(destination, "wb") as file:
            file.write(self.file)


cdef class DiskFile(UploadedFile):
    """ Implements the `DiskFile` class.

    This class is to be used for on-disk file storage after
    memory resources have been exhausted or it becomes for efficient to
    offload from memory to the disk.

    :param `filename`: (optional) The `str` name of the given file.
    :param `temp_directory`: (optional) A `str` path to a temporary
    """

    def __init__(self, filename=None, temp_directory=None):
        super().__init__(filename=filename)

        self.temp_path = os.path.join(
            temp_directory or gettempdir(), str(uuid.uuid4())
        )
        self.pointer = 0
        self.delete_on_exit = True

    def __del__(self):
        if self.delete_on_exit is True:
            try:
                os.remove(self.temporary_path)
            except FileNotFoundError:
                pass

    def seek(self, position):
        """ Sets `self.pointer` to a given position.

        :param position: An `int` position.
=       """
        self.pointer = position

    async def write(self, data):
        """ Writes byte data to the `file`.

        This method appends byte `data` to a file according
        to `self.temp_path`, then updates `self.pointer` according
        to the size of the `data`.

        :param `data`: A `bytes`-like set of `data`.
        """
        with open(self.temp_path, "ab+") as file:
            file.write(data)

        self.pointer += len(data)

    async def read(self, count=0):
        """ Reads and returns `file` contents.

        :param `count`: A `count` of characters to read.
        """
        if count:
            data = self.file[self.pointer:(self.pointer + count)]
            self.pointer += count
        else:
            data = self.file[self.pointer:]
            self.pointer = len(self.file)

        return bytes(data)

    async def save(self, destination):
        """ Saves file at `self.temp_path` to the given `destination`.

        :param `destination`: A `str` path to the desired save destination.
        """
        shutil.move(self.temp_path, destination)
        self.delete_on_exit = False


cdef class SmartFile:
    """ Implements the `SmartFile` class.

    This class mediates the usage of `DiskFile` and `MemoryFile` objects
    by monitoring memory limits and offloading file data to the disk if
    necessary or efficient.

    :param `filename`: (optional) The `str` name of the given file.
    :param `temp_dir`: (optional) The `str` path of a temporary storage location.
    :param `in_memory_limit`: (optional) An `int` limit to memory consumption.
                              The default value is 10 MiB.
    """

    def __init__(
        self,
        filename=None,
        temp_dir=None,
        in_memory_limit=10 * 1024 * 1024
    ):
        self.filename = filename
        self.temp_dir = temp_dir

        self.in_memory_limit = in_memory_limit
        self.in_memory = True

        self.buffer = bytearray()
        self.pointer = 0
        self.engine = None

    async def write(self, data):
        """ Writes file `data` to a `DiskFile`.

        This method will, if `self.in_memory` is `True` and data size
        is beyond `self.in_memory_limit`,  write data to a newly instantiated
        `DiskFile` object. If `self.in_memory` is `True`, the current
        `self.buffer` will be extended with the given data, and `self.pointer`
        will be updated accordingly. If `self.in_memory` is `False`, it will
        write data to the existing `DiskFile`, which would assumingly be
        stored as `self.engine`.

        :param `data`: A `bytearray` of file data to write.
        """
        cdef int data_size = len(data)

        if self.in_memory:

            if len(self.buffer) + data_size > self.in_memory_limit:
                self.engine = DiskFile(
                    filename=self.filename, temporary_dir=self.temp_dir
                )
                self.engine.write(self.buffer)

                self.in_memory = False
            else:
                self.buffer.extend(data)
                self.pointer += data_size

        else:
            self.engine.write(data)

    cdef object consume(self):
        """ Consumes and returns necessary resources.

        This method evaluates the state of `self` and returns a
        new `MemoryFile` object if `self.in_memory` is True and
        `self.filename` is present. If no `filename` is present, the
        decoded value of `self.buffer` is returned. Otherwise,
        `self.engine`, a `DiskFile` object, is returned with its pointer
        set back to 0.

        :return: A `MemoryFile`, decoded buffer, or `DiskFile` instance.
        """
        if self.in_memory and self.filename:
            return MemoryFile(filename=self.filename, file=self.buffer)
        elif self.in_memory:
            return self.buffer.decode()
        else:
            self.engine.seek(0)
            return self.engine


cdef class MultipartParser:
    """ Implements the `MultipartParser` class.

    This class implements a control interface for parsing multipart
    data, including file value and headers.

    :param `boundary`: a `bytes` value defining the `boundary`.
    :param `temp_dir`: a `str` path for temporary storage.
    :param `in_memory_limit`: an `int` defining the maximum memory to be consumed.
    """

    def __init__(
        self,
        bytes boundary,
        str temp_dir=None,
        int in_memory_threshold=1 * 1024 * 1024
    ):
        self.data = bytearray()
        self.values = {}
        self.temp_dir = None
        self.in_memory_threshold = in_memory_threshold

        self.start_boundary = b"--" + boundary
        self.boundary_length = len(self.start_boundary)
        self.end_boundary = b"--" + boundary + b"--" + b"\r\n"
        self.status = EXPECTING_BOUNDARY
        self.current_buffer = None

    cdef inline bytearray clean_value(self, bytearray value):
        """ Cleans a `value`.

        :param `value`: The `bytearray` `value` to clean.

        :return: The cleaned `value`, still a `bytearray`.
        """
        if value[0] == 37 or value[0] == 34:
            value = value[1:]
        elif value[-1] == 37 or value[-1] == 34:
            value = value[:-1]

        return value

    cdef void parse_header(self, bytearray header):
        """ Parses a given `header`.

        This method parses a raw set of headers into `self.values`
        by splitting the binary data into a `dict` of `parsed_values`,
        then decoding and pairing those values with a `SmartFile`.

        :param `header`: a `bytearray` `header` set.
        """
        cdef:
            dict parsed_values = {}
            bytearray value
            list pieces

        position = header.find(b"Content-Disposition: form-data;") + 31
        header = header[position:]

        values = header.strip().split(b";")
        for value in values:
            value = value.strip()
            pieces = value.split(b"=")

            if len(pieces) == 2:
                parsed_values[pieces[0].decode()] = self.clean_value(pieces[1])

        if "name" in parsed_values:
            filename = parsed_values.get("filename")

            self.current_buffer = SmartFile(
                filename=filename.decode("utf-8")
                if filename
                else None, temp_dir=self.temp_dir
            )

            self.values[parsed_values["name"].decode()] = (
                parsed_values, self.current_buffer
            )

    async def feed(self, bytes data):
        """ Feeds raw `data` into the parser.

        This method tracks through the entirety of the `data` to parse out headers
        and buffer into the parser instance. It uses three benchmarks to track
        its progress through the `data`, `EXPECTING_BOUNDARY`,
        `EXPECTING_CONTENT_HEADERS`, and `EXPECTING_BUFFER`.

        If no data is present, the function returns. If `status`
        is set to `EXPECTING_BOUNDARY`, it will track through and delete excess
        once the boundary is found, and status will be set to
        `EXPECTING_CONTENT_HEADERS`. If `status` is set to `EXPECTING_CONTENT_HEADERS`,
        the function will find and parse headers as they are encountered. Once all
        headers have been parsed, `status` will be set to `EXPECTING_BUFFER`.
        If `status` is set to `EXPECTING_BUFFER`, it will move through and write that
        content to `self.current_buffer`. Once this is complete, a terminal return is
        hit and the process is complete.

        :param data: a `bytes` object of data.
        """
        cdef:
            int position
            bytearray pending_data = self.data
            int boundary_length = self.boundary_length

        pending_data.extend(data)

        while pending_data:
            if pending_data == self.end_boundary:
                return

            elif self.status == EXPECTING_BOUNDARY:

                if len(pending_data) >= boundary_length:
                    position = pending_data.find(self.start_boundary)

                    if position != -1:
                        del pending_data[:(position + len(self.start_boundary))]

                        self.status = EXPECTING_CONTENT_HEADERS
                    else:
                        raise ValueError("Missing boundaries.")

                else:
                    return

            elif self.status == EXPECTING_CONTENT_HEADERS:
                position = pending_data.find(b"\r\n\r\n")

                if position != -1:
                    self.parse_header(pending_data[:position])
                    del pending_data[:position + 4]

                    self.status = EXPECTING_BUFFER
                else:
                    return

            elif self.status == EXPECTING_BUFFER:
                position = pending_data.find(self.start_boundary)

                if position != -1:
                    await self.current_buffer.write(pending_data[:position - 2])
                    del pending_data[:position]

                    self.current_buffer = None
                    self.status = EXPECTING_BOUNDARY

                    continue

                elif len(pending_data) >= boundary_length * 40:
                    await self.current_buffer.write(
                        pending_data[:len(pending_data) - boundary_length]
                    )

                    del pending_data[:-boundary_length]

                return

    cdef dict consume(self):
        """ Consumes all key/value pairs on the parser.

        :return: a `dict` of successfully parsed values.
        """
        cdef:
            str key
            tuple values
            dict parsed_values = {}
            SmartFile file

        for key, values in self.values.items():
            file = values[1]
            parsed_values[key] = file.consume()

        return parsed_values
