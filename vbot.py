import tav.proxy.database
import tav.bot

import os.path
import sys


PROXY_DATABASE = \
    os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'proxy.db')


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Twitch Artificial Viewers'
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
        '--score', dest='score', default=0.3, type=float,
        help='relative score of proxies to use'
    )

    parser.add_argument(
        'name', help='Twitch username'
    )

    parser.add_argument(
        'viewers', type=int, help='How many viewers/threads'
    )

    ns = parser.parse_args()

    bot = tav.bot.ViewerBot(ns.name, timeout=ns.timeout, verbose=not ns.quiet)

    with tav.proxy.database.SqliteProxyDatabase(PROXY_DATABASE) as db:
        proxies = db.load(ns.score)

    bot.proxies.add_working_proxies(proxies)

    bot.run(ns.viewers)

if __name__ == '__main__':
    main()
