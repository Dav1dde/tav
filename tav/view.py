import livestreamer.session
import concurrent.futures
import traceback
import itertools
import requests
import queue


# N worker threads, concurrent.futures.executor
#
# Idea 1:
#   * Proxy Queue
#   * Build one future per thread, when a proxy drops out,
#     let the future add a new future with a new proxy
#   * Future: (session, proxy, (url1, url2, ..., url10))
#
# Idea 2:
#   * Proxy Queue
#   * Build 10 futures per thread
#   * When the future drops out (due to shitty proxy) pop a proxy
#   * and add 10 new futures
#   * Future:
#       (session, proxy, url1)
#       (session, proxy, url2)
#       ...
#       (session, proxy, url10)
#

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:20.0) Gecko/20100101 Firefox/20.0',
    'Accept-Encoding': 'gzip, deflate',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive'
}


def tolerant(fun, max_err, err_inc, err_dec, exc=Exception):
    errors = 0

    while errors < max_err:
        try:
            yield fun()
        except exc:
            #traceback.print_exc()
            errors += err_inc
        else:
            errors = max(0, errors - err_dec)

    raise StopIteration()


class LivestreamerSession(livestreamer.session.Livestreamer):
    PLUGINS = ('twitch',)

    def load_plugin(self, name, file, pathname, desc):
        if name in self.PLUGINS:
            livestreamer.session.Livestreamer.load_plugin(
                self, name, file, pathname, desc
            )
        elif file:
            file.close()


class Idea2Viewer(object):
    def __init__(self, twitch, proxies, num_urls, timeout):
        self.twitch = twitch
        self.proxies = proxies
        self.num_urls = num_urls
        self.timeout = timeout

        self.jobs = queue.Queue()
        self.futures = list()

    def init(self, proxies):
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=proxies
        ) as executor:
            futures = [executor.submit(self.add_job) for _ in range(proxies)]

            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                print('ADDED {}/{}'.format(i+1, proxies))
                try:
                    f.result()
                except Exception:
                    traceback.print_exc()

    def add_job(self):
        urls = self.get_urls()

        for i, (proxy, url) in enumerate(urls):
            # 0 = master
            self.jobs.put((i == 0, proxy, url))

    def start(self, executor, threads):
        for i in range(threads):
            self.add_future(executor)

    def add_future(self, executor):
        def cb(future):
            try:
                result = future.result()
            except Exception as e:
                traceback.print_exc()
            self.futures.remove(future)

        future = executor.submit(self.do_work)
        future.add_done_callback(cb)
        self.futures.append(future)

    def do_work(self):
        print('WORK')
        while True:
            (master, proxy, url) = self.jobs.get()

            def fun():
                return requests.head(
                    url, proxies={'http': proxy.http}, headers=HEADERS
                )

            r = list(itertools.islice(tolerant(fun, 10, 2, 1), 1))

            print(r)

            if len(r) == 0 or r[0].status != 200:
                # no result and master that means 10 more!
                if master:
                    print('NEW')
                    self.add_job()
                else:
                    print('DROPPED OFF')
            else:
                self.jobs.put((master, proxy, url))

            self.jobs.task_done()

    def _get_urls(self, proxy):
        session = LivestreamerSession()

        session.set_option('http-proxy', proxy.http)
        session.set_option('http-headers', HEADERS)
        session.set_option('http-timeout', self.timeout)

        def get_url():
            return (proxy, session.streams(self.twitch)['worst'].url)

        urls = itertools.islice(tolerant(get_url, 3, 1, 1), self.num_urls)

        return list(urls)

    def get_urls(self):
        urls = list()
        while len(urls) < self.num_urls:
            try:
                proxy = self.proxies.get()
            except queue.Empty:
                return
            urls = self._get_urls(proxy)
            self.proxies.task_done()

        return urls

    def kickoff(self, number):
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=number
        ) as executor:
            futures = [executor.submit(self.kickoff_one) for _ in range(number)]

            #concurrent.futures.wait(futures)
            for i, f in enumerate(concurrent.futures.as_completed(futures)):
                print('ADDED {}/{}'.format(i+1, number))
                try:
                    f.result()
                except Exception:
                    traceback.print_exc()

            #for _ in range(number):
            #    print('YOLO: {}/{}'.format(_, number))
            #    #self.executor.submit(self.kickoff_one)
            #    self.kickoff_one()

            print('DONE')

    def kickoff_one(self):
        urls = self.get_urls()

        print('KICKING OFF! {} {}'.format(self.proxies.qsize(), len(urls)))
        for i, (proxy, url) in enumerate(urls):
            # first element (index 0) is master
            #print('LOL? {}'.format(i))
            self.submit(i == 0, proxy, url)

    def submit(self, master, proxy, url):
        #print('submit')
        def cb(future):
            try:
                result = future.result()
            except Exception as e:
                traceback.print_exc()
            self.futures.remove(future)

        future = self.executor.submit(self, master, proxy, url)
        future.add_done_callback(cb)
        self.futures.append(future)

    def __call__(self, master, proxy, url):
        # if master -> recreate threads

        def fun():
            return requests.head(
                url, proxies={'http': proxy.http}, headers=HEADERS
            )

        r = list(itertools.islice(tolerant(fun, 10, 2, 1), 1))

        #print('WORK {} {}'.format(proxy, r))
        if len(r) == 0:
            # no result and master that means 10 more!
            if master:
                print('NEW')
                self.kickoff_one()
            else:
                print('DROPPED OFF')
        else:
            # keep up the views
            self.submit(master, proxy, url)




