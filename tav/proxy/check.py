from tav.proxy import Proxy

from datetime import datetime
import concurrent.futures
import requests
import sys


def check_proxy(proxy, timeout):
    proxies = {
        'http': 'http://{p.ip}:{p.port}'.format(p=proxy)
    }

    before = datetime.now()
    try:
        r = requests.get(
            'http://echo.untraced.net', proxies=proxies, timeout=timeout
        )
        after = datetime.now()
        j = r.json()
    except Exception:
        return (proxy, False, 0)
    return (
        proxy,
        r.status_code == 200 and j['ip'] == proxy.ip,
        (after - before).total_seconds()
    )


def check_proxies(proxies, num_threads, timeout):
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(check_proxy, proxy, timeout) for proxy in proxies]

        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()

            yield (i, result)
