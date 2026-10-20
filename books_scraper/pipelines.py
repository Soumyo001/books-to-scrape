import math, re
from scrapy.exceptions import DropItem

class BookDataPipeline:
    """clean and normalize book items"""

    TEXT_FIELDS = (
        "title",
        "price",
        "availability",
        "product_url",
        "image_url",
        "category",
    )

    @classmethod
    def from_crawler(cls, crawler):
        """create the pipeline and update the scrapy crawler"""
        pipeline = cls()
        pipeline.crawler = crawler
        return pipeline

    def process_item(self, item):
        """normalize and reject invalid records"""

        spider = self.crawler.spider
        
        for field in self.TEXT_FIELDS:
            value = item.get(field)

            if not isinstance(value, str) or not value.strip():
                spider.logger.warning(f"Dropping item with missing or invalid field: {field}")
                raise DropItem(f"Missing or invalid field: {field}")

            item[field] = " ".join(value.split())

        price_text = re.sub(r"[^\d.,-]", "", item["price"])
        price_text = price_text.replace(",", "")

        try:
            price = float(price_text)
        except ValueError as exc:
            spider.logger.warning("Dropping item with invalid price: " + item["price"])
            raise DropItem("Invalid book price") from exc

        if not math.isfinite(price) or price < 0:
            spider.logger.warning("Dropping item with invalid numeric price: " + item["price"])
            raise DropItem("Book price must be finite and non-negative")

        item["price"] = price
        item["availability"] = item["availability"].casefold().startswith("in stock")

        spider.logger.debug("Processed book item: " + item["title"])

        return item
