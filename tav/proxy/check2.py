import threading
import requests
import queue


class ProxyChecker(threading.Thread):
    def __init__(self, queue, timeout=(5, 5), name='ProxyChecker Thread'):
        threading.Thread.__init__(self, name=name)

        self.queue = queue
        self.timeout = timeout

        self._stop = False
        self._broken = list()
        self._working = list()

    def run(self):
        self._stop = False

        while not self._stop:
            proxy = self.queue.get()
            proxies = {
                'http': 'http://{p.ip}:{p.port}'.format(p=proxy)
            }

            try:
                requests.get(
                    'http://google.com', proxies=proxies, timeout=self.timeout
                )
            except Exception:
                self._broken.append(proxy)
            else:
                self._working.append(proxy)

            self.queue.task_done()

    def stop(self):
        self._stop = True

    def result(self):
        return (self._working, self._broken)


def check_proxies_bad(proxies, num_threads, timeout=(5, 5)):
    q = queue.Queue()

    for proxy in proxies:
        q.put(proxy)

    threads = list()
    for i in range(num_threads):
        name = 'ProxyChecker {}/{} ({} proxies)'.format(
            i+1, num_threads, len(proxies)
        )
        thread = ProxyChecker(queue, timeout, name)
        thread.setDaemon(True)
        thread.start()
        threads.append(thread)

    q.join()

    working = list()
    broken = list()
    for thread in threads:
        w, b = thread.result()

        working.extend(w)
        broken.extend(b)

    return (working, broken)
