import asyncio
import sys

from crawl import crawl_site_async


async def main():
    args = sys.argv
    if len(args) < 2:
        print("no website provided")
        sys.exit(1)
    if len(args) > 2:
        print("too many arguments provided")
        sys.exit(1)

    base_url = args[1]

    page_data = await crawl_site_async(base_url, max_concurrency=10)
    print(f"finishing crawl of: {base_url}")

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

    print(f"crawled {len(page_data)} pages")

    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
