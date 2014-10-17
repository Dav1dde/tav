import tav.proxy.check
import tav.proxy

import sqlite3


class SqliteProxyDatabase(object):
    def __init__(self, path=None):
        self.path = None

        self.connection = None
        self.cursor = None

        if path is not None:
            self.connect(path)

    def connect(self, path):
        self.connection = sqlite3.connect(path)
        self.cursor = self.connection.cursor()

        self.path = path

    def disconnect(self):
        self.connection.commit()
        self.connection.close()

        self.cursor = None
        self.connection = None

    def add(self, proxy):
        self.cursor.execute('''
            INSERT INTO Proxy VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', proxy)

    def add_safe(self, proxy):
        try:
            self.add(proxy)
        except sqlite3.IntegrityError:
            pass

    def load(self, relscore=0.0):
        proxies = list()

        stmt = self.cursor.execute('''
            SELECT * FROM Proxy
            WHERE
                (checked AND (score*1.0/checked >= ?))
                OR (? == 0 AND checked == ?)
            ORDER BY score*1.0/checked DESC
        ''', (relscore, relscore, relscore))

        for row in stmt:
            proxies.append(tav.proxy.Proxy(*row))

        return proxies

    def update_score(self, num_threads, timeout, fun=None):
        proxies = self.load()
        num_proxies = len(proxies)

        for i, (proxy, works) in tav.proxy.check.check_proxies(
                proxies, num_threads, timeout):
            if fun is not None:
                fun(i, num_proxies, proxy, works)

            self.cursor.execute('''
                UPDATE Proxy SET
                    score=?, checked=(checked+1)
                WHERE ip=? AND port=?
            ''', (
                proxy.score + int(works),
                proxy.ip, proxy.port
            ))

    def __enter__(self):
        if self.connection is None:
            self.connect(self.path)

        return self

    def __exit__(self, type, value, tb):
        if self.connection is not None:
            self.disconnect()

    @staticmethod
    def create(path):
        connection = sqlite3.connect(path)
        cursor = connection.cursor()

        cursor.execute('''
            CREATE TABLE Proxy (
                ip TEXT,
                port INTEGER,

                score INTEGER,
                country TEXT,
                anonlevel TEXT,
                https BOOLEAN,

                checked INTEGER DEFAULT 0,

                PRIMARY KEY (ip, port)
            )
        ''')

        connection.commit()
        connection.close()

    @staticmethod
    def drop(path):
        connection = sqlite3.connect(path)
        cursor = connection.cursor()

        cursor.execute('''
            DROP TABLE Proxy;
        ''')

        connection.commit()
        connection.close()
