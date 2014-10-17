import tav.proxy.check
import tav.proxy.list
import tav.proxy.gather
import tav.proxy.database

import os.path
import sys


PROXY_FILE_ALL = os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'proxy', 'Proxy2.txt')
PROXY_FILE_WORKING = os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'proxy', 'Working.txt')

PROXY_DATABASE = os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'proxy.db')


def database():
    if not os.path.exists(PROXY_DATABASE):
        tav.proxy.database.SqliteProxyDatabase.create(PROXY_DATABASE)

    #tav.proxy.database.SqliteProxyDatabase.drop(PROXY_DATABASE)
    #tav.proxy.database.SqliteProxyDatabase.create(PROXY_DATABASE)

    with tav.proxy.database.SqliteProxyDatabase(PROXY_DATABASE) as db:
        for proxy in tav.proxy.gather.USProxy().get():
            db.add_safe(proxy)

        db.update_score(50, 5, fun=tav.proxy.list.ProxyList.progress_fun)


def main():
    database()

    #pl = tav.proxy.list.ProxyList.from_iterable(tav.proxy.gather.gather(), False)

    #for p in tav.proxy.gather.USProxy().get():
    #    print(p)

    #with open(PROXY_FILE_ALL, 'w') as f:
    #    pl.save_to_fobj(None, f)




if __name__ == '__main__':
    main()
