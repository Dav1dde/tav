import tav.proxy.check
import tav.proxy.list
import tav.proxy.gather
import tav.proxy.database

import os.path
import sys


PROXY_DATABASE = os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'proxy.db')


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Twitch Artificial Viewers database updater'
    )

    parser.add_argument(
        '--timeout', dest='timeout', type=int, default=5,
        help='Timeout after which a connection/proxy times out'
    )

    parser.add_argument(
        '--db', dest='database', default=PROXY_DATABASE,
        help='Path to proxy database'
    )

    parser.add_argument(
        '--quiet', dest='quiet', action='store_true',
        help='Don\'t print any status updates'
    )

    parser.add_argument(
        'threads', type=int,
        help='How many threads for checking the proxies'
    )

    ns = parser.parse_args()

    fun = tav.proxy.list.ProxyList.progress_fun
    if ns.quiet:
        fun = None

    if not os.path.exists(ns.database):
        tav.proxy.database.SqliteProxyDatabase.create(ns.database)

    with tav.proxy.database.SqliteProxyDatabase(ns.database) as db:
        for i, proxy in enumerate(tav.proxy.gather.gather()):
            if not ns.quiet:
                sys.stdout.write('[?] Adding proxy {}/? \r'.format(i+1))
                sys.stdout.flush()

            db.add_safe(proxy)

        db.update_score(ns.threads, ns.timeout, fun=fun)



if __name__ == '__main__':
    main()
