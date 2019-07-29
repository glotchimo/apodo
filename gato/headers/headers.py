"""
gato.headers.headers
~~~~~~~~~~~~~~~~~~~~

This module implements the custom Headers class.
"""


class Headers:
    """ Implements `Headers`.

    :param `raw`: a raw `list` of headers to parse.
    """

    def __init__(self, raw=None):
        self.raw = raw or []
        self.values = None
        self.evaluated = False

    def __getitem__(self, item: str):
        if not self.evaluated:
            self.eval()

        return self.values[item.lower()]

    def __setitem__(self, key: str, value: str):
        if not self.evaluated:
            self.eval()

        self.values[key.lower()] = value

    def __repr__(self):
        return f"<Headers {self.dump()}>"

    def get(self, key, default=None):
        """ Gets a given header value by `key`.

        :param `key`: A `str` key name to search for.
        :param `default`: (optional) A replaceable default return value.
        :return: The found header value.
        """
        if not self.evaluated:
            self.eval()

        return self.values.get(key.lower()) or default

    def eval(self):
        """ Evaluates and stores raw header values. """
        self.values = {}
        while self.raw:
            header = self.raw.pop()
            self.values[header[0].decode("utf-8").lower()] = header[1].decode(
                "utf-8"
            )

        self.evaluated = True

    def dump(self):
        """ Gets all headers, evaluating them if not yet done. """
        if not self.evaluated:
            self.eval()

        return self.values

    def parse_cookies(self):
        """ Parses any cookies in the headers.

        :return cookies: a `dict` of key, value cookie pairs.
        """
        header = self.get("cookie")
        cookies = {}
        if header:
            for cookie in header.split(";"):
                first = cookie.find("=")
                name = cookie[:first].strip()
                value = cookie[first + 1 :]
                cookies[name] = value

        return cookies
