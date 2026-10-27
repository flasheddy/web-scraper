# web-scraper

Async Python web crawler built as a Boot.dev guided project. It starts at a base
URL, recursively crawls same-site pages concurrently, extracts a headline, the
first paragraph, outgoing links, and image URLs from each page, then writes
everything to a sorted `report.json`.

## What it does

- Recursive crawl beginning at the base URL, restricted to the same host (exact
  `netloc` match); off-site links are collected but never followed.
- Fully async with `aiohttp`. An `asyncio.Semaphore` caps in-flight requests and
  an `asyncio.Lock` guards shared visited/page state.
- URL de-duplication via `normalize_url`: scheme dropped, host lowercased,
  trailing slash stripped (`https://Example.com/a/` → `example.com/a`).
- Hard stop once `max_pages` pages have been visited in that run; later links
  are ignored and a message is printed.
- Per page it records:

  | Field | Source |
  |---|---|
  | `url` | requested page URL |
  | `heading` | first `<h1>`, falling back to the first `<h2>`, else `""` |
  | `first_paragraph` | first `<p>` inside `<main>`, falling back to the first `<p>` on the page, else `""` |
  | `outgoing_links` | every `<a href>` resolved to an absolute URL |
  | `image_urls` | every `<img src>` resolved to an absolute URL |

- Skips responses with status >= 400, non-`text/html` content types, and network
  errors; each skip is logged and the crawl continues.
- Sends `User-Agent: BootCrawler/1.0`.

## Requirements

- Python >= 3.13
- [uv](https://docs.astral.sh/uv/)

## Install

```sh
uv sync
```

## Run

```sh
uv run main.py <base_url> [max_concurrency] [max_pages]
```

| Argument | Required | Default | Meaning |
|---|---|---|---|
| `base_url` | yes | — | Page the crawl starts from, e.g. `https://example.com` |
| `max_concurrency` | no | `1` | Max simultaneous in-flight requests |
| `max_pages` | no | `5` | Max pages to crawl before stopping |

Defaults live in `config.py` (`MAX_CONCURRENCY`, `MAX_PAGES`). Both numeric
arguments must be positive integers, otherwise the program prints an error and
exits with status 1.

Examples:

```sh
# defaults: 1 concurrent request, 5 pages
uv run main.py https://example.com

# cap concurrency at 5, crawl up to 100 pages
uv run main.py https://example.com 5 100
```

The default concurrency of 1 makes the crawler serial; raise it explicitly to
crawl faster.

## Output

`report.json` is written to the current working directory as an array sorted by
page URL:

```json
[
  {
    "url": "https://example.com",
    "heading": "Example Domain",
    "first_paragraph": "This domain is for use in illustrative examples.",
    "outgoing_links": ["https://www.iana.org/domains/example"],
    "image_urls": []
  }
]
```

If nothing was crawled, no file is written and a message is printed instead.

## Tests

```sh
uv run python -m unittest -v
```

Covers URL normalization and the HTML extraction helpers (`test_crawl.py`).

## Project layout

| File | Purpose |
|---|---|
| `main.py` | CLI entry point: argument parsing, orchestration, exit codes |
| `crawl.py` | `AsyncCrawler` (async fetch, concurrency, limits) and HTML extraction helpers |
| `json_report.py` | Serializes page data to `report.json` |
| `config.py` | Default `max_concurrency` and `max_pages` |
| `test_crawl.py` | Unit tests for normalization and extraction |
| `report.json` | Generated crawl output (gitignored) |
| `.gitignore` | Ignores `__pycache__/`, `.venv/`, `report.json`, and other build artifacts |
