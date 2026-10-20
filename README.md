# Books to Scrape — Scrapy Data Pipeline

A Scrapy project that collects a random sample of books from [Books to Scrape](https://books.toscrape.com/index.html), cleans the data, exports it to JSON, CSV, and XML, and saves the same records to SQLite. The project can run locally or through Scrapyd inside Docker.

## 1. Project Overview

The spider starts from the website's homepage and discovers the available book categories automatically. It chooses a random target of **5–10 categories**, visits each selected category and all its listing pages, and collects the unique product links. A category containing fewer than five books is skipped and replaced with another randomly chosen category.

After finding enough eligible categories, the spider randomly chooses **exactly five different books from each** and visits their product pages. The results are cleaned through a Scrapy Item Pipeline, saved to SQLite, and exported using Scrapy Feed Exports.

A successful run therefore produces **25–50 book records**, depending on the number of selected categories. The exact categories and books change between runs. This selection follows the category-sampling approach clarified for the assignment; it does not scrape five books from every category on the site.

## 2. Features

- Discovers category names and URLs from the homepage without hardcoding them.
- Follows category pagination to collect unique book URLs before sampling.
- Randomly chooses 5–10 eligible categories, with replacements for categories containing fewer than five books.
- Randomly selects five unique books per eligible category.
- Extracts the six required fields: `title`, `price`, `availability`, `product_url`, `image_url`, and `category`.
- Removes extra whitespace, converts prices to numbers, and normalizes availability to a Boolean.
- Validates records and writes them to SQLite through `BookDataPipeline`.
- Exports the processed records to `books.json`, `books.csv`, and `books.xml` using the `FEEDS` setting.
- Includes logging for category discovery, selection, crawling, processing, and errors.
- Supports local execution and deployment through the Scrapyd HTTP API in Docker.

## 3. Tech Stack

| Tool | Version / purpose |
| --- | --- |
| Python | 3.12 |
| Scrapy | 2.19.0 — requests, spiders, Items, Pipelines, Feed Exports |
| SQLite | Built into Python through `sqlite3` — database storage |
| Docker | Containerized runtime for Scrapyd and the crawler |
| Scrapyd | 1.6.0 — job scheduling and execution through HTTP |
| scrapyd-client | 2.0.3 — packages and deploys the Scrapy project |
| HTML/CSS selectors and XPath | Extract data from website pages |

The Python package versions are defined in `requirements.txt`. Docker was tested with Docker Engine 29.9.1 on Ubuntu Linux; other compatible Docker versions may also work.

## 4. Installation Guide

### Requirements

- Python 3.12 and `pip`
- Internet access to `https://books.toscrape.com/`
- Docker Engine, if using the containerized Scrapyd setup
- `curl` for the Scrapyd API examples

From the project directory on Ubuntu/Linux:

```bash
cd books-scrapy-assignment
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Confirm the spider is available:

```bash
scrapy list
```

Expected spider name: `books`.

## 5. Environment Setup

The project uses `books_scraper/settings.py` for Scrapy configuration and `scrapy.cfg` for the settings module and Scrapyd deployment target.

Important settings:

| Setting | Purpose |
| --- | --- |
| `ROBOTSTXT_OBEY = True` | Follows the website's available robots.txt rules. |
| `CONCURRENT_REQUESTS_PER_DOMAIN = 1` | Limits concurrent requests to the target domain. |
| `DOWNLOAD_DELAY = 1` | Adds a delay between requests. |
| `ITEM_PIPELINES` | Enables `books_scraper.pipelines.BookDataPipeline`. |
| `FEEDS` | Defines the JSON, CSV, and XML exports with overwrite enabled. |
| `FEED_EXPORT_ENCODING = "utf-8"` | Writes UTF-8 exports. |

The following environment variables are optional:

| Variable | Local default | Docker value |
| --- | --- | --- |
| `BOOKS_DATABASE_PATH` | `<project>/data/books.db` | `/app/data/books.db` |
| `BOOKS_OUTPUT_DIR` | `.` (current working directory) | `/app/data` |

For example, to put local feed exports in a chosen directory:

```bash
mkdir -p output
BOOKS_OUTPUT_DIR=output scrapy crawl books
```

If setting `BOOKS_DATABASE_PATH` yourself, supply a writable file path. The pipeline creates its parent directory when the spider opens.

The deployment URL in `scrapy.cfg` is `http://127.0.0.1:6800/`, so the example commands assume Scrapyd is accessible on that address.

## 6. Running the Spider

Activate the virtual environment, navigate to the project root, and run:

```bash
source .venv/bin/activate
scrapy crawl books
```

With the default local settings, the results are written to:

```text
books.json
books.csv
books.xml
data/books.db
```

The console log reports category discovery, pagination, selected books, processing activity, and the final crawl statistics. A successful crawl should include `finish_reason: finished` and an `item_scraped_count` matching the saved record count. Because selection is random, the count can vary from 25 to 50. A finished job alone does not guarantee a complete dataset if individual requests fail; check the item count and warnings as well.

Run the spider **without** `-o` or `-O` to use the three Feed Exports already defined in `settings.py`.

## 7. Docker Setup Guide

The Dockerfile uses `python:3.12-slim`, installs the dependencies, copies the Scrapy project, and starts Scrapyd on port `6800`. The database and exports are written to `/app/data` and made available on the host through a bind mount.

Run the following commands from the project root:

```bash
mkdir -p data

docker build -t books-scrapyd .

docker run -d \
  --name books-scrapyd \
  -p 127.0.0.1:6800:6800 \
  -v "$PWD/data:/app/data" \
  books-scrapyd
```

Check the container and Scrapyd service:

```bash
docker ps
docker logs books-scrapyd
curl -fsS http://127.0.0.1:6800/daemonstatus.json
```

The API should return JSON containing `"status": "ok"`. This confirms the server is responding; the spider still needs to be deployed and scheduled as described below.

To stop and restart the existing container:

```bash
docker stop books-scrapyd
docker start books-scrapyd
```

If a container with that name already exists and you need to replace it after rebuilding the image, stop and remove the old container first:

```bash
docker stop books-scrapyd
docker rm books-scrapyd
```

Then repeat the `docker run` command. The host `data/` directory remains in place, but Scrapyd projects deployed inside the removed container must be deployed again.

The container currently runs as root, so files it creates in `data/` may be owned by root on Linux. This can affect editing files or running a local crawl after a Docker crawl. Resolve file permissions on the host if necessary; do not run two crawls against the same SQLite database at the same time.

## 8. Scrapyd Deployment Guide

Scrapyd runs inside the Docker container. Its `scrapyd.conf` enables the HTTP service on port `6800` and leaves `items_dir` empty so that Scrapy's own `FEEDS` configuration writes all three required export formats instead of being replaced by Scrapyd's automatic JSON Lines feed.

Start the container before deploying. With the virtual environment active, run from the project root:

```bash
scrapyd-deploy
```

Check the deployed project and spider:

```bash
curl -fsS http://127.0.0.1:6800/listprojects.json
curl -fsS "http://127.0.0.1:6800/listspiders.json?project=books_scraper"
```

The responses should include the project `books_scraper` and the spider `books`.

Schedule a crawl through the Scrapyd API:

```bash
curl -fsS -X POST \
  http://127.0.0.1:6800/schedule.json \
  -d project=books_scraper \
  -d spider=books \
  | tee scrapyd-schedule.json
```

A successful response includes `"status": "ok"` and a unique `jobid`. Check its status:

```bash
curl -fsS \
  "http://127.0.0.1:6800/listjobs.json?project=books_scraper"
```

Repeat this request until the scheduled job ID appears under `finished`. To download the corresponding job log:

```bash
JOB_ID=$(python -c 'import json; print(json.load(open("scrapyd-schedule.json"))["jobid"])')

curl -fsS \
  "http://127.0.0.1:6800/logs/books_scraper/books/$JOB_ID.log" \
  -o scrapyd-job.log
```

Verify the log contains `finish_reason: finished`, the number of scraped items, the SQLite record count, and separate successful JSON, CSV, and XML feed-export messages. For a Docker-run spider, the outputs are on the host at:

```text
data/books.json
data/books.csv
data/books.xml
data/books.db
```

The deployed application, Scrapyd logs, and uploaded project versions are stored in the container. The bind mount persists only `data/`; replacing the container requires redeploying the project.

## 9. Output Format Description

Each exported record contains exactly these six fields:

| Field | Meaning | Normalized representation |
| --- | --- | --- |
| `title` | Book title | String with normalized whitespace |
| `price` | Book price | Non-negative numeric value, without the currency symbol |
| `availability` | Book stock status | `true` or `false` |
| `product_url` | Book detail page | Absolute URL |
| `image_url` | Book cover image | Absolute URL |
| `category` | Category selected for the book | String with normalized whitespace |

Example JSON record (illustrative, not a claim about a particular crawl):

```json
{
  "title": "Example Book",
  "price": 12.5,
  "availability": true,
  "product_url": "https://books.toscrape.com/catalogue/example-book/index.html",
  "image_url": "https://books.toscrape.com/media/cache/example.jpg",
  "category": "Example Category"
}
```

The three exports contain the same processed item data. JSON represents prices as numbers and availability as Booleans. CSV and XML represent those values as text (`True`/`False` and numeric strings). SQLite stores availability as `1` or `0`. These are format differences, not different stock statuses.

All three export files are overwritten on each crawl. The file locations are controlled by `BOOKS_OUTPUT_DIR`.

## 10. Database Configuration

The project uses SQLite through Python's built-in `sqlite3` module. The `BookDataPipeline` opens the database, creates the `books` table if needed, validates items, inserts them using parameterized SQL statements, and commits the records when the spider closes.

The table structure is:

```sql
CREATE TABLE IF NOT EXISTS books (
    title TEXT NOT NULL,
    price REAL NOT NULL CHECK (price >= 0),
    availability INTEGER NOT NULL CHECK (availability IN (0, 1)),
    product_url TEXT NOT NULL,
    image_url TEXT NOT NULL,
    category TEXT NOT NULL,
    PRIMARY KEY (product_url, category)
);
```

The composite primary key prevents duplicate entries for the same product URL and category. Invalid or duplicate records are rejected by the pipeline, with warnings recorded in the crawl logs.

**Important:** The pipeline clears the table at the start of every crawl. SQLite therefore holds the latest run's records, not a history of every run. Back up `data/books.db` before starting a new crawl if the previous data must be kept.

To check the database's record count and internal integrity, run from the project root:

```bash
python - <<'PY'
import sqlite3

with sqlite3.connect("data/books.db") as connection:
    count = connection.execute("SELECT COUNT(*) FROM books").fetchone()[0]
    integrity = connection.execute("PRAGMA integrity_check").fetchone()[0]

print("Book records:", count)
print("SQLite integrity:", integrity)
PY
```

A healthy database returns `SQLite integrity: ok`. This checks SQLite's internal consistency; it does **not** by itself prove that database rows match the three exports.

To compare all four datasets, run the following from the project root **after a completed crawl**. Set `output_dir` to `Path(".")` for a local crawl or `Path("data")` for the Docker/Scrapyd crawl:

```python
import csv
import json
import sqlite3
import xml.etree.ElementTree as ET
from collections import Counter
from decimal import Decimal
from pathlib import Path

output_dir = Path("data")  # Change to Path(".") for a local crawl.
database_path = Path("data/books.db")

with (output_dir / "books.json").open(encoding="utf-8") as f:
    json_rows = json.load(f)
with (output_dir / "books.csv").open(encoding="utf-8", newline="") as f:
    csv_rows = list(csv.DictReader(f))
xml_rows = [
    {child.tag: child.text for child in item}
    for item in ET.parse(output_dir / "books.xml").getroot().findall("item")
]
with sqlite3.connect(database_path) as connection:
    connection.row_factory = sqlite3.Row
    db_rows = [dict(row) for row in connection.execute("SELECT * FROM books")]

fields = {"title", "price", "availability", "product_url", "image_url", "category"}

def normalized(row):
    assert set(row) == fields
    value = str(row["availability"]).strip().lower()
    assert value in {"true", "false", "1", "0"}
    return (
        row["title"],
        Decimal(str(row["price"])),
        value in {"true", "1"},
        row["product_url"],
        row["image_url"],
        row["category"],
    )

datasets = {"JSON": json_rows, "CSV": csv_rows, "XML": xml_rows, "SQLite": db_rows}
reference = Counter(normalized(row) for row in json_rows)

for name, rows in datasets.items():
    assert Counter(normalized(row) for row in rows) == reference, f"{name} differs"
    print(f"{name}: {len(rows)} records")

category_counts = Counter(row["category"] for row in json_rows)
assert 5 <= len(category_counts) <= 10
assert all(count == 5 for count in category_counts.values())
assert len({(r["category"], r["product_url"]) for r in json_rows}) == len(json_rows)
print("All formats match and each category has five unique books.")
```

This comparison is only meaningful when the three exports and SQLite database are from the **same completed crawl**; don't compare old local exports against a newer Docker-run database.

## 11. Architecture Diagram

```text
Books to Scrape homepage
         |
         v
Discover category names and URLs (parse)
         |
         v
Choose a random target of 5-10 categories
         |
         v
Visit each category and paginate (parse_category)
         |
         +--> Fewer than 5 unique books? --> Try another category
         |
         v
Randomly select 5 book URLs per eligible category
         |
         v
Visit product pages (parse_book)
         |
         v
BookItem (6 fields)
         |
         v
BookDataPipeline: clean, validate, insert into SQLite
         |
         +--> SQLite: data/books.db
         |
         v
Scrapy Feed Exports: books.json / books.csv / books.xml
```

Scrapyd provides HTTP-based deployment and job scheduling around the same Scrapy application. Docker runs the Scrapyd service and makes the generated output files available through the mounted `data/` directory.

## 12. Folder Structure

```text
books-scrapy-assignment/
├── books_scraper/
│   ├── __init__.py
│   ├── spiders/
│   │   ├── __init__.py
│   │   └── books_spider.py    # Category discovery, pagination, selection, extraction
│   ├── items.py              # Required book fields
│   ├── pipelines.py          # Cleaning, validation, and SQLite insertion
│   ├── settings.py           # Scrapy, database, and Feed Export settings
│   └── middlewares.py        # Generated middleware boilerplate; not enabled
├── data/                     # Generated database and Docker-run exports
├── scrapy.cfg                # Scrapy settings module and deployment address
├── scrapyd.conf              # Scrapyd server configuration
├── setup.py                  # Python packaging metadata for scrapyd-deploy
├── Dockerfile                # Container image and Scrapyd startup
├── requirements.txt          # Pinned Python dependencies
├── .dockerignore             # Excludes unnecessary files from the image build
├── .gitignore                # Excludes generated development files
├── LICENSE
└── README.md
```

Generated directories such as `.venv/`, `__pycache__/`, `build/`, and `project.egg-info/` are not part of the maintained application code. Packaging tools may regenerate some of them when deploying.

## 13. Design Decisions

- **Dynamic discovery:** Category links are extracted from the homepage, so the scraper does not depend on a manually maintained category list.
- **Random sampling after pagination:** The spider gathers all candidate book URLs within an eligible category before choosing five. This avoids sampling only from the first listing page.
- **Replacement categories:** Categories with fewer than five unique books are skipped so that selected eligible categories each contribute five books.
- **Scrapy Items and Pipelines:** `BookItem` defines the data fields; `BookDataPipeline` normalizes, validates, and stores each record. The same processed item is then available to Feed Exports.
- **SQLite:** A lightweight database requiring no separate server, suitable for this assignment's sample size.
- **Composite key and input validation:** The database constrains invalid numeric/Boolean values and rejects repeated product/category pairs.
- **Feed Exports in settings:** All three output formats are configured centrally with the same ordered fields and overwrite enabled.
- **Containerized Scrapyd:** Provides repeatable dependencies and an API for scheduling crawls. The bind mount keeps exports and SQLite outside the container.
- **Responsible crawling:** Requests are limited to one concurrent request per domain with a one-second download delay.

## 14. Known Limitations

- The spider depends on the current HTML layout and selectors of Books to Scrape. Site changes may require selector updates.
- Category and book selection is random; results and record counts differ between runs. No fixed random seed is configured.
- The database and exports are refreshed each crawl; previous datasets are not retained automatically.
- Failed product requests, unavailable pages, or dropped items may cause fewer than the expected 5 books per category. Review crawl stats and logs after each run.
- The availability conversion recognizes `In stock` and `In stock (N available)`; other values are treated as out of stock.
- A successful Scrapyd scheduling response does not mean the crawl succeeded. Check the finished job's log and output counts.
- The Scrapyd server is configured for local development and the Docker port is published only on `127.0.0.1`. No Scrapyd authentication is configured. Do not expose this endpoint directly to an untrusted network.
- Docker-created output files may be owned by root on Linux, which can affect later local runs or file edits.
- Replacing the Docker container removes deployed Scrapyd projects and logs stored inside that container. The mounted `data/` files remain on the host.
