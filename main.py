import asyncio
import sys

from config import MAX_CONCURRENCY, MAX_PAGES
from crawl import crawl_site_async
from json_report import write_json_report


async def main():
    args = sys.argv
    if len(args) < 2:
        print("no website provided")
        sys.exit(1)
    if len(args) > 4:
        print("too many arguments provided")
        sys.exit(1)

    match len(args):
        case 3:
            if not is_valid_arg(args[2]):
                print("Make sure type a positive max concurrency integer")
                sys.exit(1)
            max_concurrency = int(args[2])
            print(f"no max pages provided, default to {MAX_PAGES}")
            max_pages = MAX_PAGES
        case 4:
            if not is_valid_arg(args[2]):
                print("Make sure type a positive max concurrency integer")
                sys.exit(1)
            max_concurrency = int(args[2])
            if not is_valid_arg(args[3]):
                print("Make sure type a positive max page integer")
                sys.exit(1)
            max_pages = int(args[3])
        case _:
            print(
                f"no max concurrency and max pages provided, default to {MAX_CONCURRENCY}, and {MAX_PAGES} respectively"
            )
            max_concurrency = MAX_CONCURRENCY
            max_pages = MAX_PAGES

    base_url = args[1]

    page_data = await crawl_site_async(
        base_url, max_concurrency=max_concurrency, max_pages=max_pages
    )
    print(f"Crawling complete. Found {len(page_data)} pages.")

    write_json_report(page_data)

    sys.exit(0)


def is_valid_arg(arg: str) -> bool:
    return arg.isdigit() and int(arg) > 0


if __name__ == "__main__":
    asyncio.run(main())
