import scrapy, random
from books_scraper.items import BookItem

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
            raise ValueError(f"Found only {len(category_links)} categories. at least 5 required.")

        categories = []

        for link in category_links:
            category_name = link.xpath("normalize-space(.)").get()
            category_url = response.urljoin(link.attrib["href"])
            categories.append((category_name, category_url))

        category_urls = [url for _, url in categories]

        if len(set(category_urls)) != len(category_urls):
            raise ValueError("Duplicate category URLs found.")

        target_count = random.randint(5, min(10, len(categories)))
        initial_categories = random.sample(categories, target_count)

        remaining_categories = [
            category
            for category in categories
            if category not in initial_categories
        ]

        replacement_categories = random.sample(
            remaining_categories,
            len(remaining_categories),
        )

        self.target_category_count = target_count
        self.initial_category_urls = {
            url for _, url in initial_categories
        }
        self.category_queue = initial_categories + replacement_categories
        self.eligible_categories = {}

        self.logger.info(f"Discovered {len(categories)} categories")
        self.logger.info(
            f"Initial random selection: {target_count} categories: " +
            ", ".join(name for name, _ in initial_categories)
        )

        yield self._request_next_category(response)

    def _request_next_category(self, response):
        """schedule the next selected category or a replacement"""

        if not self.category_queue:
            message = (
                f"Only {len(self.eligible_categories)} eligible categories "
                f"found; target was {self.target_category_count}."
            )
            self.logger.error(message)
            raise ValueError(message)

        category_name, category_url = self.category_queue.pop(0)

        if category_url in self.initial_category_urls:
            self.logger.info(f"Crawling selected category: {category_name}")
        else:
            self.logger.info(f"Trying replacement category: {category_name}")

        return response.follow(
            category_url,
            callback=self.parse_category,
            cb_kwargs={
                "category_name": category_name,
                "category_url": category_url,
                "book_urls": set(),
                "page_count": 0,
            },
        )

    def parse_category(self, response, category_name, category_url, book_urls, page_count):
        """Collect unique book urls for a category"""

        books = response.css("article.product_pod")
        if not books:
            raise ValueError(f"No book cards found on {response.url}")

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
                    "category_url": category_url,
                    "book_urls": book_urls,
                    "page_count": page_count,
                },
            )
            return

        book_count = len(book_urls)

        self.logger.info(f"Completed {category_name}: {page_count} pages, {book_count} unique books")

        if book_count >= 5:
            self.eligible_categories[category_url] = {
                "name": category_name,
                "book_urls": sorted(book_urls),
                "page_count": page_count,
            }

            self.logger.info(f"Eligible categories: {len(self.eligible_categories)}/{self.target_category_count}")
        else:
            self.logger.warning(f"Category {category_name} has only {book_count} books. trying a replacement")

        if len(self.eligible_categories) >= self.target_category_count:
            self.logger.info(f"Target reached: {self.target_category_count} eligible categories")

            for category in self.eligible_categories.values():
                self.logger.info(
                    "Eligible: %s (%d candidate books)",
                    category["name"],
                    len(category["book_urls"]),
                )

                selected_book_urls = random.sample(category["book_urls"], 5)
                self.logger.info(
                    "Selected 5 books from category: %s",
                    category["name"],
                )

                for book_url in selected_book_urls:
                    yield response.follow(
                        book_url,
                        callback=self.parse_book,
                        cb_kwargs={
                            "category_name": category["name"],
                        },
                    )
            return

        yield self._request_next_category(response)

    def parse_book(self, response, category_name):
        """Extract the six required fields from a selected book page."""

        title = response.css("div.product_main h1::text").get()
        price = response.css("div.product_main p.price_color::text").get()
        availability = response.css("div.product_main p.availability").xpath("normalize-space(.)").get()
        image_src = response.css("div.item.active img::attr(src)").get()

        if not all((title, price, availability, image_src)):
            self.logger.error(f"Missing required product data on {response.url}")
            raise ValueError(f"Required product data missing on {response.url}")

        item = BookItem(
            title=title,
            price=price,
            availability=availability,
            product_url=response.url,
            image_url=response.urljoin(image_src),
            category=category_name,
        )

        self.logger.info(f"Extracted book '{title}' from category '{category_name}'")

        yield item