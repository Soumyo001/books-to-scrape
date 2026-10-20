# Books to Scrape — Scrapy Project

## 1. Project Overview

A Scrapy project that collects book information from [Books to Scrape](https://books.toscrape.com/index.html).

The spider discovers categories, randomly selects 5–10 eligible categories, and extracts five random books from each selected category. The results are saved in JSON, CSV, XML, and SQLite.

## 2. Features

- Discovers book categories automatically.
- Handles category pagination.
- Randomly selects 5–10 categories and five books from each.
- Replaces categories containing fewer than five books.
- Cleans and validates data using a Scrapy Item Pipeline.
- Exports JSON, CSV, and XML files.
- Stores records in SQLite.
- Supports Docker and Scrapyd deployment.

## 3. Tech Stack

| Technology | Version | Purpose |
|---|---|---|
| Python | 3.12 | Programming language |
| Scrapy | 2.19.0 | Web scraping and data extraction |
| SQLite | Built-in Python module | Database storage |
| Docker | 29.9.1 | Containerization |
| Scrapyd | 1.6.0 | Spider deployment and execution |
| scrapyd-client | 2.0.3 | Deploying the Scrapy project to Scrapyd |

## 4. Installation Guide

Make sure Python 3.12 is installed.

Open a terminal in the directory containing the project folder and run:

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

The `scrapy.cfg` file contains the Scrapy settings module and Scrapyd deployment address.

## 6. Running the Spider

From the project root, run:

```bash
source .venv/bin/activate
scrapy list
scrapy crawl books
```

Wait until the crawl finishes.

Check the generated files:

```bash
ls -lh books.json books.csv books.xml data/books.db
```

Each successful crawl selects between 5 and 10 eligible categories, producing 25–50 book records.

## 7. Docker Setup Guide

Make sure Docker is installed and running.

From the project root, run these commands in order:

```bash
mkdir -p data
```

Build the image:

```bash
docker build -t books-scrapyd .
```

Start the container:

```bash
docker run -d \
  --name books-scrapyd \
  -p 127.0.0.1:6800:6800 \
  -v "$PWD/data:/app/data" \
  books-scrapyd
```

Check the container:

```bash
docker ps
```

Check the Scrapyd server:

```bash
curl -fsS http://127.0.0.1:6800/daemonstatus.json
```

The response should contain `"status": "ok"`.

To stop the container:

```bash
docker stop books-scrapyd
```

To start the existing container again:

```bash
docker start books-scrapyd
```

## 8. Scrapyd Deployment Guide

Make sure the Docker container is running and the virtual environment is activated.

Deploy the Scrapy project:

```bash
scrapyd-deploy
```

Check the deployed project:

```bash
curl -fsS http://127.0.0.1:6800/listprojects.json
```

Check the available spiders:

```bash
curl -fsS "http://127.0.0.1:6800/listspiders.json?project=books_scraper"
```

Run the spider through the Scrapyd API:

```bash
curl -fsS -X POST \
  http://127.0.0.1:6800/schedule.json \
  -d project=books_scraper \
  -d spider=books
```

The response contains a `jobid`.

Check the job status:

```bash
curl -fsS "http://127.0.0.1:6800/listjobs.json?project=books_scraper"
```

Repeat the status command until the job appears under `finished`.

To view the crawl log, replace `JOB_ID` with the returned job ID:

```bash
curl -fsS "http://127.0.0.1:6800/logs/books_scraper/books/JOB_ID.log"
```

After the crawl finishes, check the files:

```bash
ls -lh data/books.json data/books.csv data/books.xml data/books.db
```

## 9. Output Format Description

The project generates three export files:

- `books.json`
- `books.csv`
- `books.xml`

Each book contains six fields:

| Field | Description |
|---|---|
| `title` | Book title |
| `price` | Numeric price without the currency symbol |
| `availability` | Boolean stock status |
| `product_url` | Full product page URL |
| `image_url` | Full book image URL |
| `category` | Book category |

The exports contain the same book information. Data types may be represented differently depending on the file format.

## 10. Database Configuration

The project uses SQLite, with the database stored at:

```text
data/books.db
```

The Item Pipeline creates and maintains a table named `books`.

The table stores the six required book fields. The combination of `product_url` and `category` is used as the primary key to prevent duplicate records.

Before each new crawl, the pipeline clears the existing records and stores the results of the new crawl.

The database path can be changed using the `BOOKS_DATABASE_PATH` environment variable.

## 11. Architecture Diagram (Text or Image)

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

## 12. Folder Structure

```text
books-scrapy-assignment/
|
|-- books_scraper/
|   |-- spiders/
|   |   |-- books_spider.py
|   |-- items.py
|   |-- pipelines.py
|   |-- middlewares.py
|   |-- settings.py
|
|-- data/
|-- Dockerfile
|-- requirements.txt
|-- scrapy.cfg
|-- scrapyd.conf
|-- setup.py
|-- .dockerignore
|-- .gitignore
|-- README.md
```

## 13. Design Decisions

- Scrapy is used for crawling, pagination, and book extraction.
- Categories and book URLs are discovered dynamically instead of being hardcoded.
- Random sampling is performed after collecting book URLs.
- An Item Pipeline handles data cleaning, validation, and database insertion.
- SQLite is used because it is lightweight and requires no separate database server.
- Scrapy Feed Exports handle JSON, CSV, and XML output.
- Docker and Scrapyd are used to deploy and execute the spider.

## 14. Known Limitations

- The spider depends on the HTML structure of Books to Scrape.
- Selected categories and books change between runs because selection is random.
- The SQLite database stores the latest crawl rather than previous crawl history.
- Failed requests may reduce the number of successfully scraped books.
- The Docker configuration exposes Scrapyd only on the local machine.