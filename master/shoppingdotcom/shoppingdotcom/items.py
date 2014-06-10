# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

from scrapy.item import Item, Field

class ShoppingdotcomItem(Item):
    # define the fields for your item here like:
    # name = Field()
    categories = Field()
    product_name = Field()
    prices = Field()
    stores = Field()
    image_urls = Field()
    product_urls = Field()
    pass
