import tav.bot

import os.path


PROXY_FILE_ALL = os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'proxy', 'Proxy.txt')
PROXY_FILE_WORKING = os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'proxy', 'Working.txt')


def main():
    bot = tav.bot.ViewerBot('sprachverliebt', verbose=True)
#    bot.proxies.add_file(PROXY_FILE_ALL, False)
#    bot.check(500)

#    with open(PROXY_FILE_WORKING, 'w') as f:
#        bot.proxies.save_to_fobj(f, None)

    bot.proxies.add_file(PROXY_FILE_WORKING, False)

    bot.run(500, 250, 500)

if __name__ == '__main__':
    main()
