FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BOOKS_DATABASE_PATH=/app/data/books.db \
    BOOKS_OUTPUT_DIR=/app/data

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip check

COPY scrapy.cfg .
COPY books_scraper/ ./books_scraper/
COPY scrapyd.conf /etc/scrapyd/scrapyd.conf

RUN mkdir -p /app/data \
    /var/lib/scrapyd/eggs \
    /var/lib/scrapyd/logs \
    /var/lib/scrapyd/items \
    /var/lib/scrapyd/dbs

EXPOSE 6800

CMD ["scrapyd"]
