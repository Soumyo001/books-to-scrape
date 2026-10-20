import math, re, sqlite3
from pathlib import Path
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

    def __init__(self):
        """set initial db values"""

        self.connection = None
        self.items_saved = 0

    @classmethod
    def from_crawler(cls, crawler):
        """create the pipeline and update the scrapy crawler"""
        pipeline = cls()
        pipeline.crawler = crawler
        pipeline.database_path = Path(
            crawler.settings.get("BOOKS_DATABASE_PATH")
        )
        return pipeline

    def open_spider(self):
        """connect the SQLite database and create books table"""

        spider = self.crawler.spider

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.connection = sqlite3.connect(self.database_path)

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS books (
                title TEXT NOT NULL,
                price REAL NOT NULL CHECK (price >= 0),
                availability INTEGER NOT NULL
                    CHECK (availability IN (0, 1)),
                product_url TEXT NOT NULL,
                image_url TEXT NOT NULL,
                category TEXT NOT NULL,
                PRIMARY KEY (product_url, category)
            )
            """
        )

        self.connection.execute("DELETE FROM books")
        self.connection.commit()

        self.items_saved = 0

        spider.logger.info(
            "SQLite database ready at %s",
            self.database_path,
        )

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
        except ValueError as e:
            spider.logger.warning("Dropping item with invalid price: " + item["price"])
            raise DropItem("Invalid book price") from e

        if not math.isfinite(price) or price < 0:
            spider.logger.warning("Dropping item with invalid numeric price: " + item["price"])
            raise DropItem("Book price must be finite and non-negative")

        item["price"] = price
        status = item["availability"].casefold()

        item["availability"] = re.fullmatch(
            r"in stock(?: \(\d+ available\))?",
            status,
        ) is not None

        try:
            self.connection.execute(
                """
                INSERT INTO books (
                    title,
                    price,
                    availability,
                    product_url,
                    image_url,
                    category
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    item["title"],
                    item["price"],
                    int(item["availability"]),
                    item["product_url"],
                    item["image_url"],
                    item["category"],
                ),
            )
        except sqlite3.IntegrityError as e:
            spider.logger.warning("Dropping duplicate or invalid database record: " + item["product_url"])
            raise DropItem("Duplicate book record") from e

        self.items_saved += 1

        spider.logger.debug("Processed and stored book item: " + item["title"])

        return item

    def close_spider(self):
        """commit stored records and close the database connection"""

        spider = self.crawler.spider
        
        if self.connection is None:
            return

        self.connection.commit()
        self.connection.close()
        self.connection = None

        spider.logger.info(f"Stored {self.items_saved} book records in {self.database_path}")
