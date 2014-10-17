from collections.abc import Sequence
import re


class Proxy(Sequence):
    __slots__ = (
        'ip', 'port', 'score', 'country', 'anonlevel', 'https', 'checked'
    )

    def __init__(self, ip, port, score=0,
                 country=None, anonlevel=None, https=False, checked=0):
        self.ip = ip
        self.port = int(port)

        self.score = score
        self.country = country
        self.anonlevel = anonlevel
        self.https = bool(https)

        self.checked = int(checked)

    def is_valid(self):
        return re.match('^(\d{1,3}\.){3}\d{1,3}$', self.ip) is not None

    def __str__(self):
        return '{}:{}'.format(self.ip, self.port)

    def __unicode__(self):
        return self.__str__()

    def __repr__(self):
        return (
            'Proxy({self.ip!r}, {self.port!r}, score={self.score!r}, '
            'country={self.country!r}, anonlevel={self.anonlevel!r}, '
            'https={self.https!r}, checked={self.checked!r})'.format(self=self)
        )

    def __getitem__(self, key):
        name = self.__slots__[key]
        return getattr(self, name)

    def __len__(self):
        return len(self.__slots__)


