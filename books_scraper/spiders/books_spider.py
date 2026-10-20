import scrapy, random

class BooksSpider(scrapy.Spider):
    """Discover all book categories from homepage"""

    name = "books"
    allowed_domains = ["books.toscrape.com"]
    start_urls = ["https://books.toscrape.com/index.html"]

    def parse(self, response):
        """Discover all category and randomly select 5-10"""

        category_links = response.css(
            ".side_categories > ul > li > ul > li > a[href]"
        )
        if len(category_links) < 5:
            self.logger.error(f"found only {len(category_links)} categories")
            raise ValueError("At least 5 categories required")

        categories = []

        for link in category_links:
            category_name = link.xpath("normalize-space(.)").get()
            category_url = response.urljoin(link.attrib["href"])
            categories.append((category_name, category_url))

        if len({url for _, url in categories}) != len(categories):
            raise ValueError("Duplicate category URLs found")

        selected_count = random.randint(5, min(10, len(categories)))
        selected_categories = random.sample(categories, selected_count)

        self.logger.info(f"Discovered {len(categories)} categories")
        self.logger.info(f"Randomly selected {selected_count} categories")

        for category_name, category_url in selected_categories:
            self.logger.info(f"Selected category: {category_name}")

            yield response.follow(
                category_url, 
                callback=self.parse_category,
                cb_kwargs={
                    "category_name": category_name,
                    "book_urls": set(),
                    "page_count": 0,
                },
            )

    def parse_category(self, response, category_name, book_urls, page_count):
        """Collect unique book urls for a category"""

        books = response.css("article.product_pod")
        if not books:
            self.logger.error(f"No books found on {response.url}")
            raise ValueError("category page contains no book cards")

        for book in books:
            book_href = book.css("h3 a::attr(href)").get()
            if not book_href:
                raise ValueError(f"Missing book URL on {response.url}")

            book_urls.add(response.urljoin(book_href))

        page_count += 1
        next_page = response.css("li.next a::attr(href)").get()

        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse_category,
                cb_kwargs={
                    "category_name": category_name,
                    "book_urls": book_urls,
                    "page_count": page_count,
                }
            )
        else:
            self.logger.info(f"Completed {category_name}: {page_count} pages, {len(book_urls)} unique books")
            if len(book_urls) < 5:
                self.logger.warning(f"Category {category_name} has fewer than 5 books: {len(book_urls)}")
            