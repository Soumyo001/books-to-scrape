
import scrapy


class BookItem(scrapy.Item):
    """store the required fields extracted from a selected book."""

    title = scrapy.Field()
    price = scrapy.Field()
    availability = scrapy.Field()
    product_url = scrapy.Field()
    image_url = scrapy.Field()
    category = scrapy.Field()