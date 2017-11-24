# -*- coding: utf-8 -*-
import re

import scrapy
from scrapy.http import Request
from proxy_pool.items import ProxyPoolItem


USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3)\
    AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36"
EXPRESION_RE = re.compile(r"var\s+\w+\s+=([^;]+);")
DIGIT_RE = re.compile(r"[.0-9]+")


def parse_script(script):
    expresions = EXPRESION_RE.findall(script)
    ip_front = DIGIT_RE.search(expresions[0]).group(0)[::-1]
    ip_rear = DIGIT_RE.search(expresions[1]).group(0)
    ip = ip_front + ip_rear
    # Warning: not secure string
    port = str(eval(expresions[2].strip()))
    return ip, port


class ProxydbSpider(scrapy.Spider):
    name = 'proxydb'
    start_url = 'http://proxydb.net/?protocol=http&protocol=https&offset=0'
    max_page = 100

    def __init__(self, *args, **kwargs):
        super(ProxydbSpider, self).__init__(*args, **kwargs)
        self.index_page = 1

    def start_requests(self):
        return [Request(self.start_url, headers={'user-agent': USER_AGENT})]

    def parse(self, response):
        info = response.xpath('/html/body/div[2]/table/tbody/tr')
        for x in info:
            ip_script = x.xpath('td[1]/script/text()').extract()[0]
            item = ProxyPoolItem()
            item['ip'], item['port'] = parse_script(ip_script)
            item['protocol'] = x.xpath('td[2]/text()').extract()[0].strip()
            item['address'] = x.xpath('td[3]/abbr/text()').extract()[0]
            item['types'] = x.xpath('td[4]/span/text()').extract()[0]
            item['website'] = 'proxydb.net'
            yield item
        next_url = response.xpath('/html/body/div[2]/nav/a[2]/@href').extract()[0]
        if self.index_page < self.max_page and next_url:
            self.index_page += 1
            yield Request('http://proxydb.net' + next_url, self.parse,
                          headers={'user-agent': USER_AGENT})
