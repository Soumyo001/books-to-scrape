import scrapy

class BooksSpider(scrapy.Spider):
    """Discover all book categories from homepage"""

    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/index.html"]

    def parse(self, response):
        """Discover and log all book categories from homepage"""

        category_links = response.css(
            ".side_categories > ul > li > ul > li > a[href]"
        )
        if not category_links:
            self.logger.error(f"No categories found on {response.url}")
            raise ValueError("No book categories were discovered")

        self.logger.info(f"Discovered {len(category_links)} categories")

        for link in category_links:
            category_name = link.xpath("normalize-space(.)").get()
            category_url = response.urljoin(link.attrib["href"])

            self.logger.info(f"Category: {category_name}, {category_url}")