import tav.proxy.database
import tav.bot

import os.path
import sys


PROXY_DATABASE = os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'proxy.db')


def main():
    bot = tav.bot.ViewerBot(sys.argv[1], timeout=1, verbose=True)
#    bot.proxies.add_file(PROXY_FILE_ALL, False)
#    bot.check(750)

#    with open(PROXY_FILE_WORKING, 'w') as f:
#        bot.proxies.save_to_fobj(f, None)

    with tav.proxy.database.SqliteProxyDatabase(PROXY_DATABASE) as db:
        proxies = db.load(0.5)

    bot.proxies.add_working_proxies(proxies)

    bot.run(200)

if __name__ == '__main__':
    main()
