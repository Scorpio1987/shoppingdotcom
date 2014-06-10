from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import Selector
from scrapy.item import Item
from scrapy.http import Request
from urllib2 import urlparse
from shoppingdotcom.items import ShoppingdotcomItem
from BeautifulSoup import *
import re

class ShoppingDotComSpider(CrawlSpider):

    name = "shopping"
    allowed_domains = ["shopping.com"]
    start_urls = ["http://www.shopping.com/xSN"]

    """This function reads the first page for the category URLS and
    yeilds a Request and as a callback this provides parse_products"""
    def parse_start_url(self, response):
        print response.url
        sel = Selector(response)
        
        for url in sel.xpath("//a"):
            #print url.xpath("@href").extract()
            href = url.xpath("@href").extract()[0] if url.xpath("@href").extract() else None
            if href and href.split("/")[-1] == "products":
                yield Request(urlparse.urljoin(response.url, href), callback=self.parse_products)
            if href and href.find("xFA-") >= 0:
                href = href.replace("xFA-", "").split("~")[0]+"/products"
                yield Request(urlparse.urljoin(response.url, href), callback=self.parse_products)
            pass

    """This function parses actual product information. If there are more than one store for the
    product then we need to go to the next page to read all stores and their prices. So this is
    handled using different function parse_multiple_store_product. This function yeilds items and requests"""
    def parse_products(self, response):
        print "parse_products", response.url
        sel = Selector(response)
        breadcrumb = sel.xpath('//div[contains(@class,"breadCrumb")]')
        categories = [span for span in breadcrumb.xpath(".//span[@itemprop='title']/text()").extract()[1:]]
        categories.append(breadcrumb.xpath(".//span/text()").extract()[-1])
        print categories
        
        for product in sel.xpath('//div[contains(@id,"quickLookItem")]'):
            # check if it is a multistore product
            if product.xpath('.//span[contains(@id, "numStoresQA")]'):
                print product.xpath(".//a/@href").extract()[0]
                url = product.xpath(".//a/@href").extract()[0]
                url = "/".join(url.split("/")[:-1])+"/prices"
                yield Request(urlparse.urljoin(response.url, url), callback=self.parse_multiple_store_product)
            else:
                # It is not a multistore product. Parse it.
                item = ShoppingdotcomItem()
                item["categories"] = categories
                item["product_name"] = product.xpath(".//span[contains(@id, 'nameQA')]/@title").extract()[0]
                if product.xpath(".//span[@class='placeholderImg']").extract():
                    item["image_urls"] = product.xpath(".//span[@class='placeholderImg']/text()").extract()
                else:
                    item["image_urls"] = product.xpath(".//div[@class='gridItemTop']//img/@src").extract()
                item["product_urls"] = [urlparse.urljoin(response.url, product.xpath(".//a/@href").extract()[0])]
                item["stores"] = product.xpath(".//a[@class='newMerchantName']/text()").extract()
                item["prices"] = [price.replace("\n","") for price in product.xpath(".//span[@class='productPrice']/a/text()").extract()]
                yield item

        # Check if Next page link is there then yeild request with next URL
        if sel.xpath("//a[@name='PLN']").extract():
            yield Request(urlparse.urljoin(response.url, sel.xpath("//a[@name='PLN']/@href").extract()[0]), self.parse_products)
            pass
        
    def parse_multiple_store_product(self, response):
        print "parse_multiple_store_product", response.url
        sel = Selector(response)
        breadcrumb = sel.xpath('//div[contains(@class,"breadCrumb")]')
        categories = [span for span in breadcrumb.xpath(".//span[@itemprop='title']/text()").extract()[1:]]
        print categories
        item = ShoppingdotcomItem()
        item["categories"] = categories
        item["product_name"] = sel.xpath("//h1[@class='productTitle']/text()").extract()[0]
        item["image_urls"] = list(set(sel.xpath("//div[@class='imgBorder']//img/@src").extract()))
        item["product_urls"] = []
        item["stores"] = []
        item["prices"] = []
        for div in sel.xpath("//div[contains(@id,'offerItem-')]"):
            item["product_urls"].append(urlparse.urljoin(response.url, div.xpath(".//a[@class='visitBtn']/@href").extract()[0]))
            item["stores"].append(div.xpath(".//img[contains(@id,'DCTmerchLogo')]/@title").extract()[0])
            if div.xpath(".//span[contains(@class,'toSalePrice')]"):
                item["prices"].append(re.findall("\S+\d+\.\d+", div.xpath(".//span[contains(@class,'toSalePrice')]/text()").extract()[0])[0])
            else:
                item["prices"].append(re.findall("\S+\d+\.\d+", div.xpath(".//span[contains(@id,'priceQA')]/text()").extract()[0])[0])
        yield item
        pass
