import sys

import requests


def main():
    args = sys.argv
    if len(args) < 2:
        print("no website provided")
        sys.exit(1)
    if len(args) > 2:
        print("too many arguments provided")
        sys.exit(1)

    base_url = args[1]

    print(f"starting crawl of: {base_url}...")
    print(get_html(base_url))

    sys.exit(0)


def get_html(url: str) -> str | None:
    try:
        response = requests.get(url, headers={"User-Agent": "BootCrawler/1.0"})
    except Exception as e:  # noqa: BLE001
        raise Exception(f"network error while fetching {url}: {e}")  # noqa: TRY002

    if response.status_code > 399:
        raise Exception(f"got HTTP error: {response.status_code} {response.reason}")  # noqa: TRY002

    content_type = response.headers.get("content-type", "")
    if "text/html" not in content_type:
        raise Exception(f"got not-HTML response: {content_type}")  # noqa: TRY002

    return response.text


if __name__ == "__main__":
    main()
