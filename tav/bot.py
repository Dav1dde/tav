from tav.exception import ViewerBotException
from tav.proxy.list import ProxyList

import concurrent.futures
import livestreamer
import traceback
import requests
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
    def __init__(self, twitch, verbose=False):
        self.twitch = twitch
        self.url = 'twitch.tv/{}'.format(self.twitch)
        self.verbose = verbose

        self.proxies = ProxyList(fun=ProxyList.progress_fun if verbose else None)

    def check(self, max_threads=75):
        self.print('[+] Checking proxies')
        total, working = self.proxies.check_proxies(max_threads, timeout=5)
        self.print('\n[+] {} of {} proxies work!'.format(working, total))
        self.print('[+] Using {} working proxies'.format(len(self.proxies)))

    def run(self, viewers, viewer_threads, proxy_threads=100):
        if self.proxies.has_unchecked():
            self.check(proxy_threads)

        if viewers > len(self.proxies):
            raise ViewerBotException(
                'Not enough working proxies ({}) for {} viewers'.format(
                    len(self.proxies), viewers
                )
            )

        if viewer_threads > viewers:
            viewer_threads = viewers

        print('[+] Launching {} viewer-threads for {} viewers'.format(viewer_threads, viewers))

        all_proxies = list(self.proxies)
        used_proxies = ProxyList.from_iterable(all_proxies[:viewers], True)
        unused_proxies = ProxyList.from_iterable(all_proxies[viewers:], True)
        new_proxies = 0

        errors = list()
        with concurrent.futures.ThreadPoolExecutor(max_workers=viewer_threads) as executor:
            futures = [executor.submit(self.view, self.proxies.get()) for i in range(viewers)]

            for i, future in enumerate(concurrent.futures.as_completed(futures)):
                (url, proxy) = (None, None)
                try:
                    (url, proxy) = future.result()
                except Exception as e:
#                    pass
                    errors.append(e)
                    traceback.print_exc()

                if url is None:
                    if len(unused_proxies) == 0:
                        self.print('[!] No more proxies!')
                        continue

                    new_proxies += 1
                    self.print_raw('[?] {} - Another connection dropped out ... \r'.format(new_proxies))
                    proxy = unused_proxies.pop()

                futures.append(executor.submit(self.view, proxy, url))

        print(errors[0])

    def view(self, proxy, url=None):
        httpproxy = 'http://{p.ip}:{p.port}'.format(p=proxy)

        session = livestreamer.Livestreamer()
        session.set_option('http-proxy', httpproxy)

        if url is None:
            try:
                stream = session.streams(self.url)
                url = stream['worst'].url
            except Exception:
                return (None, None)

        requests.head(url, headers=HEADERS, proxies={'http': httpproxy})

        return url, proxy

    def print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def print_raw(self, *args, **kwargs):
        if self.verbose:
            sys.stdout.write(*args, **kwargs)
            sys.stdout.flush()
