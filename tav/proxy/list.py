from tav.proxy import Proxy
import tav.proxy.check

from itertools import chain
import sys


class ProxyList(object):
    def __init__(self, fun=None):
        self.fun = fun

        self._working = list()
        self._unchecked = list()

        self._current_index = 0

    @classmethod
    def from_file(cls, path, working, *args, **kwargs):
        c = cls(*args, **kwargs)
        c.add_file(path, working)
        return c

    @classmethod
    def from_iterable(cls, iterable, working, *args, **kwargs):
        c = cls(*args, **kwargs)
        c.add_many(iterable, working)
        return c

    @staticmethod
    def progress_fun(current, max, working, proxy):
        sys.stdout.write('[?] Checking proxy {}/{} \r'.format(current+1, max))
        sys.stdout.flush()

    def __iter__(self):
        return iter(self._working)

    def __len__(self):
        return len(self._working)

    def get(self):
        ret = self._working[self._current_index]
        self._current_index = (self._current_index + 1) % len(self._working)
        return ret

    def pop(self):
        ret = self._working.pop()
        self._current_index = (self._current_index + 1) % len(self._working)
        return ret

    def has_unchecked(self):
        return len(self._unchecked) > 0

    def add_file(self, path, working):
        with open(path, 'r') as f:
            for line in f:
                ip, port = line.strip().split(':')
                self.add(Proxy(ip, port, 'Unknown', -1), working)

    def save_to_fobj(self, working, unchecked):
        for fobj, proxies in [
            (working, self._working),
            (unchecked, self._unchecked)
        ]:
            if fobj is not None:
                for proxy in proxies:
                    working.write('{}:{}\n'.format(proxy.ip, proxy.port))

    def add(self, proxy, working):
        if working:
            return self.add_working_proxy(proxy)
        return self.add_proxy(proxy)

    def add_many(self, proxies, working):
        if working:
            return self.add_working_proxies(proxies)
        return self.add_proxies(proxies)

    def add_proxy(self, proxy):
        self._unchecked.append(proxy)

    def add_proxies(self, proxies):
        self._unchecked.extend(proxies)

    def add_working_proxy(self, proxy):
        self._working.append(proxy)

    def add_working_proxies(self, proxies):
        self._working.extend(proxies)

    def check_proxies(self, max_threads=50, timeout=(3,3), fun=None):
        fun = self.fun if fun is None else fun

        num_proxies = len(self._unchecked)
        working = 0

        for i, proxy in tav.proxy.check.check_proxies(self._unchecked, max_threads, timeout):
            if fun is not None:
                fun(i, num_proxies, *proxy)

            works, proxy = proxy
            if works:
                self._working.append(proxy)
                working += 1

            self._unchecked.remove(proxy)

        return num_proxies, working



