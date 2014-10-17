import tav.proxy.check
import tav.proxy.list
import tav.proxy.gather

import os.path
import sys


PROXY_FILE_ALL = os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'proxy', 'Proxy2.txt')
PROXY_FILE_WORKING = os.path.join(os.path.abspath(os.path.split(__file__)[0]), 'proxy', 'Working.txt')


def main():
    pl = tav.proxy.list.ProxyList.from_iterable(tav.proxy.gather.gather(), False)

    with open(PROXY_FILE_ALL, 'w') as f:
        pl.save_to_fobj(None, f)




if __name__ == '__main__':
    main()
