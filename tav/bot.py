from tav.exception import ViewerBotException
from tav.proxy.list import ProxyList
import tav.view

import concurrent.futures
import livestreamer
import functools
import traceback
import requests
import queue
import time
import sys

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0',
    'Accept-Encoding': 'gzip, deflate',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive'
}


class ViewerBot(object):
    def __init__(self, twitch, timeout=3, verbose=False):
        self.twitch = twitch
        self.url = 'twitch.tv/{}'.format(self.twitch)

        s = livestreamer.streams(self.url)
        if len(s) == 0:
            raise ViewerBotException('Stream offline!?')

        self.timeout = timeout
        self.verbose = verbose

        self.proxies = ProxyList(fun=ProxyList.progress_fun if verbose else None)

    def check(self, max_threads=75):
        self.print('[+] Checking proxies')
        total, working = self.proxies.check_proxies(max_threads, timeout=self.timeout)
        self.print('\n[+] {} of {} proxies work!'.format(working, total))
        self.print('[+] Using {} working proxies'.format(len(self.proxies)))

    def run(self, threads, proxies, num_urls):
        if proxies*num_urls > len(self.proxies):
            raise ViewerBotException(
                'Not enough working proxies ({}) for {} viewers'.format(
                    len(self.proxies), proxies*num_urls
                )
            )

        self.print('[+] Launching {} threads'.format(threads))

        proxy_queue = queue.Queue()
        for proxy in self.proxies:
            proxy_queue.put(proxy)

        print(proxy_queue.qsize())

        viewer = tav.view.Idea2Viewer(
            self.url, proxy_queue, num_urls, self.timeout
        )
        viewer.init(proxies)

        print(viewer.jobs.qsize())

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=threads
        ) as executor:
            viewer.start(executor, threads)

            while proxy_queue.qsize() > 0:
                self.print_raw('[?] {} proxies left | {}  \n'.format(proxy_queue.qsize(), viewer.jobs.qsize()))
                time.sleep(1.0)

            print('STARTED')
        print('DONE')

    def print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def print_raw(self, *args, **kwargs):
        if self.verbose:
            sys.stdout.write(*args, **kwargs)
            sys.stdout.flush()
