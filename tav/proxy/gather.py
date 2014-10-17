from tav.proxy import Proxy

from itertools import chain
from lxml import html
import requests
import re


def gather():
    return filter(
        Proxy.is_valid,
        chain(
            GatherProxy().get(),
            USProxy().get(),
            UKProxy().get(),
            Samair().get()
        )
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
        ProxyGatherer.__init__(self)

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

            yield Proxy(
                ip, port,
                country=country.text, anonlevel=anonlevel.text,
                source=self.__class__.__name__
            )

    @staticmethod
    def extract_script_text(element):
        return re.search(r'[\d, \.]{2,}', element.findtext('script')).group(0)


class USProxy(ProxyGatherer):
    URL = 'http://www.us-proxy.org'

    def __init__(self):
        ProxyGatherer.__init__(self)

    def get(self):
        r = requests.get(self.URL)
        h = html.document_fromstring(r.text)
        entries = h.cssselect('#proxylisttable tr:nth-child(n+2)')

        for (ip, port, country, country_long,
             anonlevel, google, https, last_update) in entries:
            yield Proxy(
                ip.text, port.text, country=country_long.text,
                anonlevel=anonlevel.text, https=(https.text.lower() == 'yes'),
                source=self.__class__.__name__
            )


class UKProxy(USProxy):
    URL = 'http://free-proxy-list.net/uk-proxy.html'


class Samair(ProxyGatherer):
    URL = 'http://www.samair.ru/proxy/'

    def __init__(self):
        ProxyGatherer.__init__(self)

    def get(self):
        h = html.parse(self.URL).getroot()
        h.make_links_absolute(self.URL)
        urls = set(
            re.sub('-(\d)\.', '-0\\1.', e.get('href'))
            for e in h.cssselect('.page')
        )

        for url in urls:
            h = html.parse(url).getroot()
            h.make_links_absolute(self.URL)

            h.cssselect('#advcenter')[0].getparent().drop_tree()
            entries = h.cssselect('#proxylist tr:nth-child(n+2)')
            data_url = h.cssselect('#ipportonly > a')[0].get('href')

            h = html.parse(data_url).getroot()
            data = h.cssselect('#content pre')[0].text

            for i, line in enumerate(data.splitlines()):
                ip, port = line.split(':')

                yield Proxy(
                    ip, port,
                    country=entries[i][3].text, anonlevel=entries[i][1].text,
                    source=self.__class__.__name__
                )


