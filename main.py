import tav.bot

import os.path
import sys


PROXY_FILE_ALL = os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'proxy', 'Proxy2.txt')
PROXY_FILE_WORKING = os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'proxy', 'Working.txt')


def main():
    bot = tav.bot.ViewerBot(sys.argv[1], verbose=True)
#    bot.proxies.add_file(PROXY_FILE_ALL, False)
#    bot.check(750)

#    with open(PROXY_FILE_WORKING, 'w') as f:
#        bot.proxies.save_to_fobj(f, None)

    bot.proxies.add_file(PROXY_FILE_WORKING, False)
    bot.proxies.add_file(PROXY_FILE_ALL, False)

    bot.run(400, 400, 750)

if __name__ == '__main__':
    main()
