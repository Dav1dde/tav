from tav.proxy import Proxy

from itertools import chain
from lxml import html
import requests
import re


def gather():
    return chain(
        GatherProxy().get()
    )


def load_from_files(paths):
    proxies = list()

    for path in paths:
        with open(path, 'r') as f:
            for line in f:
                ip, port = line.split(':')
                proxies.append(Proxy(ip, int(port), 'Unknown', -1))

    return proxies


class ProxyGatherer(object):
    def get(self):
        raise NotImplementedError('get not implemented')


class GatherProxy(ProxyGatherer):
    URL = 'http://www.gatherproxy.com/proxylist/country/'
    COUNTRY_URL = 'http://www.gatherproxy.com/proxylistbycountry'

    def __init__(self, countries=None):
        self.countries = countries
        if self.countries is None:
            self.countries = list(self.get_country_list())

    def get_country_list(self):
        r = requests.get('http://www.gatherproxy.com/proxylistbycountry')

        h = html.document_fromstring(r.text)

        for e in h.cssselect('.pc-list li a'):
            yield re.match('[^\(]+', e.text).group(0).strip()

    def get(self):
#        print(self.countries)
        for country in self.countries:
            #print(country)
            r = requests.post(
                GatherProxy.URL, data={'Country': country, 'PageIdx': 1}
            )

            h = html.document_fromstring(r.text)
            try:
                num_sites = int(h.cssselect('.pagenavi a:last-child')[0].text)
            except (ValueError, IndexError):
                num_sites = 1

            for idx in range(1, num_sites+1):
                for p in self.get_proxies(country, idx):
                    yield p

    def get_proxies(self, country, idx):
        r = requests.post(
            GatherProxy.URL, data={'Country': country, 'PageIdx': idx}
        )

        h = html.document_fromstring(r.text)
        entries = h.cssselect('table tr:nth-child(n+3)')

        for (last_update, ip, port, anonlevel,
             country, city, uptime, response_time) in entries:
            ip = self.extract_script_text(ip)
            port = self.extract_script_text(port)
            ms = int(response_time.text.rstrip('ms'))

            yield Proxy(ip, port, country, ms)

    @staticmethod
    def extract_script_text(element):
        return re.search(r'[\d, \.]{2,}', element.findtext('script')).group(0)
