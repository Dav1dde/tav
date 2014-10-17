from tav.exception import ViewerBotException
from tav.proxy.list import ProxyList

import concurrent.futures
import livestreamer
import functools
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

TIMEOUT = 5

class ViewerBot(object):
    def __init__(self, twitch, verbose=False):
        self.twitch = twitch
        self.url = 'twitch.tv/{}'.format(self.twitch)
        self.verbose = verbose

        self.proxies = ProxyList(fun=ProxyList.progress_fun if verbose else None)

    def check(self, max_threads=75):
        self.print('[+] Checking proxies')
        total, working = self.proxies.check_proxies(max_threads, timeout=TIMEOUT)
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

        proxies = ProxyList.from_iterable(iter(self.proxies), True)

        errors = list()
        with concurrent.futures.ThreadPoolExecutor(max_workers=viewer_threads) as executor:
            futures = list()

            def callback(session, future):
                try:
                    futures.remove(future)
                except ValueError:
                    # TODO find out why
                    pass

                try:
                    (url, proxy) = future.result()
                except Exception as e:
                    #traceback.print_exc()
                    errors.append(e)
                    (url, proxy) = (None, None)

                if proxy is None:
                    if len(proxies) == 0:
                        self.print_raw('[!] No more proxies! {} still running                  \r'.format(len(futures)))
                        return

                    self.print_raw('[?] Another connection dropped out ... {} proxies left            \r'.format(len(proxies)))
                    proxy = proxies.pop()

                future = executor.submit(self.view, proxy, session)
                future.add_done_callback(functools.partial(callback, session))
                futures.append(future)

            for i in range(viewers):
                session = livestreamer.Livestreamer()
                future = executor.submit(self.view, proxies.pop(), session)

                future.add_done_callback(functools.partial(callback, session))
                futures.append(future)

            while len(futures) > 0:
                try:
                    time.sleep(1.0)
                except KeyError:
                    self.print('\n[+] Stopping ...')
                    break

            self.print('\n[!] {} Errors'.format(len(errors)))

            for error in errors:
                self.print(error)

    def view(self, proxy, session, url=None, timeout=TIMEOUT):
        httpproxy = 'http://{p.ip}:{p.port}'.format(p=proxy)

        if url is None:
            session.set_option('http-proxy', httpproxy)
            session.set_option('http-headers', HEADERS)
            session.set_option('http-timeout', timeout)

            try:
                stream = session.streams(self.url)
                url = stream['worst'].url
            except Exception:
                return (None, None)

        #fd = stream['worst'].open()

        errors = 0
        while errors < 500:
            try:
                requests.head(
                    url, headers=HEADERS, proxies={'http': httpproxy}, timeout=timeout
                )
            except Exception:
                errors += 10
            else:
                errors -= 1

            time.sleep(0.3)

        return (None, None)

    def print(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def print_raw(self, *args, **kwargs):
        if self.verbose:
            sys.stdout.write(*args, **kwargs)
            sys.stdout.flush()
