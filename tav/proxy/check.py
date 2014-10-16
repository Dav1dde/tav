from tav.proxy import Proxy

import concurrent.futures
import requests
import sys


def check_proxy(proxy, timeout):
    proxies = {
        'http': 'http://{p.ip}:{p.port}'.format(p=proxy)
    }

    try:
        r = requests.get(
            'http://google.com', proxies=proxies, timeout=timeout
        )
    except Exception:
        return (False, proxy)
    return (r.status_code == 200, proxy)


def check_proxies(proxies, num_threads, timeout):
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(check_proxy, proxy, timeout) for proxy in proxies]

        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()

            yield (i, result)








