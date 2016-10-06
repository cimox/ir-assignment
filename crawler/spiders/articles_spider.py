import scrapy
import re


class ArticlesSpider(scrapy.Spider):
    name = "articles"
    allowed_domains = [
        'theverge.com',
        'wired.com',
        'theguardian.com',
        'mashable.com'
    ]
    start_urls = [
        'http://theverge.com',
        'https://www.wired.com/',
        'https://www.theguardian.com/',
        'http://mashable.com/'
    ]
    pattern = 'http://www.theverge.com/[0-9]{4}/[0-9]{1,2}/[0-9]{1,2}/[0-9]{8}/.*|' \
              'https://www.wired.com/[0-9]{4}/[0-9]{2}/.*|' \
              'https://www.theguardian.com/.*/[0-9]{4}/[a-z]{2,4}/[0-9]{2}/.*|' \
              'http://mashable.com/[0-9]{4}/[0-9]{1,2}/[0-9]{2}/.*'
    regex = re.compile(pattern)

    def parse(self, response):
        result = {}
        url = response.xpath('//link[@rel="canonical"]/@href').extract_first()
        result['title'] = response.xpath('//meta[@property="og:title"]/@content').extract_first()
        result['author'] = response.xpath('//meta[@name="author"]/@content|//meta[@name="Author"]/@content').extract()
        result['timestamp'] = response.xpath(
            '//meta[@property="article:published_time"]/@content|'
            '//meta[@itemprop="datePublished"]/@content|'
            '//meta[@property="og:article:published_time"]/@content') \
            .extract_first()
        result['image_link'] = response.xpath('//meta[@property="og:image"]/@content').extract_first()
        result['url'] = url

        if 'theverge.com' in url:
            result['article'] = ''.join(response.xpath('//p[not(@class)]/text()').extract()).replace('\n', ' ')
            result['categories'] = response.xpath('(//div[@class="l-segment"]/div/*/ul)[1]/li/a/span/text()').extract()
        elif 'wired.com' in url:
            result['article'] = ''.join(
                response.xpath('(//article[@itemprop="articleBody"])[1]/p[not(@class)]/text()')
                    .extract()).replace('\n', ' ')
            result['categories'] = response.xpath('//meta[@name="news_keywords"]/@content').extract()
        elif 'theguardian.com' in url:
            result['article'] = ''.join(response.xpath('//div[@itemprop="articleBody"]/p/text()')
                                        .extract()).replace('\n', ' ')
            result['categories'] = response.xpath('//div[@data-component="keywords"]/ul/li/a/text()').extract()
        elif 'mashable.com' in url:
            result['article'] = ''.join(response.xpath('//section[@class="article-content"]/p/text()')
                                        .extract()).replace('\n', ' ')
            result['categories'] = response.xpath('//footer[@class="article-topics"]/a/text()').extract()

        yield result

        for url in response.xpath('//a/@href').re(self.pattern):
            if url is not None:
                next_page = response.urljoin(url)
                yield scrapy.Request(next_page, callback=self.parse)