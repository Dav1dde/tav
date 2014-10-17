from tav.exception import ViewerBotException
from tav.proxy.list import ProxyList

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

    def run(self, viewers):
        if viewers > len(self.proxies):
            raise ViewerBotException(
                'Not enough working proxies ({}) for {} viewers'.format(
                    len(self.proxies), viewers
                )
            )

        self.print('[+] Launching {} viewer-threads'.format(viewers))

        proxy_queue = queue.Queue()
        for proxy in self.proxies:
            proxy_queue.put(proxy)

        errors = list()
        with concurrent.futures.ThreadPoolExecutor(max_workers=viewers) as executor:
            futures = list()

            def done_callback(future):
                try:
                    result = future.result()
                except Exception as e:
                    traceback.print_exc()
                    errors.append(e)

                futures.remove(future)
                self.print_raw('[?] Connection dropped out. {} left                       \r'.format(len(futures)))

            for _ in range(viewers):
                future = executor.submit(self.view_future, proxy_queue)
                future.add_done_callback(done_callback)
                futures.append(future)

            while len(futures) > 0 and proxy_queue.qsize() > 0:
                self.print_raw('[?] {} proxies left                                   \r'.format(proxy_queue.qsize()))
                time.sleep(1.0)

        self.print('\n[!] {} Errors'.format(len(errors)))

        #for error in errors:
        #    self.print(error)

    def view(self, proxy, session):
        httpproxy = 'http://{}'.format(proxy)

        errors = 0
        while errors < 50:
            session.set_option('http-proxy', httpproxy)
            session.set_option('http-headers', HEADERS)
            session.set_option('http-timeout', self.timeout)

            try:
                stream = session.streams(self.url)
                url = stream['worst'].url
            except Exception:
                errors += 5
            else:
                break
        else:
            # no break -> no url -> broken proxy
            return

        errors = 0
        while errors < 50:
            try:
                requests.head(
                    url, headers=HEADERS,
                    proxies={'http': httpproxy}, timeout=self.timeout
                )
            except Exception:
                errors += 2
            else:
                errors = max(0, errors - 1)

            time.sleep(0.5)

    def view_future(self, proxy_queue):
        session = livestreamer.Livestreamer()

        try:
            while True:
                self.view(proxy_queue.get(True, 0.5), session)
        except queue.Empty:
            pass

    def print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def print_raw(self, *args, **kwargs):
        if self.verbose:
            sys.stdout.write(*args, **kwargs)
            sys.stdout.flush()
