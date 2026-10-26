import sys
from urllib.parse import urlsplit

import requests

from crawl import PageData, extract_page_data, normalize_url


def main():
    args = sys.argv
    if len(args) < 2:
        print("no website provided")
        sys.exit(1)
    if len(args) > 2:
        print("too many arguments provided")
        sys.exit(1)

    base_url = args[1]

    page_data = crawl_page(base_url)
    print(f"finishing crawl of: {base_url}")
    if page_data is None:
        sys.exit(0)

    print(f"crawled {len(page_data)} pages")
    for val in page_data.values():
        url = val["url"]
        heading = val["heading"]
        first_paragraph = val["first_paragraph"]
        outgoing_links = val["outgoing_links"]
        image_urls = val["image_urls"]
        report = [
            f"url: {url}",
            f"heading: {heading}",
            f"first paragraph: {first_paragraph}",
            f"outgoing links: {outgoing_links}",
            f"image urls: {image_urls}",
        ]
        print("\n".join(report))

    sys.exit(0)


def get_html(url: str) -> str | None:
    try:
        response = requests.get(
            url, headers={"User-Agent": "BootCrawler/1.0"}, timeout=10
        )
    except Exception as e:  # noqa: BLE001
        raise Exception(f"network error while fetching {url}: {e}")  # noqa: TRY002

    if response.status_code > 399:
        raise Exception(f"got HTTP error: {response.status_code} {response.reason}")  # noqa: TRY002

    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type:
        raise Exception(f"got not-HTML response: {content_type}")  # noqa: TRY002

    return response.text


def crawl_page(
    base_url: str,
    current_url: str | None = None,
    page_data: dict[str, PageData] | None = None,
) -> dict[str, PageData] | None:
    if current_url is None:
        current_url = base_url
    if page_data is None:
        page_data = {}

    base_url_obj = urlsplit(base_url)
    current_url_obj = urlsplit(current_url)
    if current_url_obj.netloc != base_url_obj.netloc:
        return page_data

    normalized_url = normalize_url(current_url)

    if normalized_url in page_data:
        return page_data

    print(f"crawling of: {current_url}...")
    try:
        html = get_html(current_url)
    except Exception as e:  # noqa: BLE001
        print(f"skipping {current_url}: {e}")
        return page_data
    if html is None:
        return page_data

    page_info = extract_page_data(html, current_url)
    page_data[normalized_url] = page_info

    for link in page_info["outgoing_links"] or []:
        _ = crawl_page(base_url, link, page_data)

    return page_data


if __name__ == "__main__":
    main()
