import asyncio
from asyncio import Lock, Semaphore, Task
from types import TracebackType
from typing import Self, TypedDict
from urllib.parse import urljoin, urlsplit

from aiohttp import ClientError, ClientSession
from bs4 import BeautifulSoup, Tag


class PageData(TypedDict):
    url: str
    heading: str
    first_paragraph: str
    outgoing_links: list[str] | None
    image_urls: list[str] | None


class AsyncCrawler:
    def __init__(self, base_url: str, max_concurrency: int, max_pages: int) -> None:
        self.base_url: str = base_url
        self.base_domain: str = urlsplit(base_url).netloc
        self.page_data: dict[str, PageData] = {}
        self.visited: set[str] = set()
        self.lock: Lock = Lock()
        self.max_concurrency: int = max_concurrency
        self.semaphore: Semaphore = Semaphore(max_concurrency)
        self.session: ClientSession | None = None
        self.max_pages: int = max_pages
        self.should_stop: bool = False
        self.all_tasks: set[Task[None]] = set()

    async def __aenter__(self) -> Self:
        self.session = ClientSession()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self.session is not None:
            await self.session.close()

    async def add_page_visit(self, normalized_url: str) -> bool:
        async with self.lock:
            if self.should_stop:
                return False
            if normalized_url in self.visited:
                return False
            if len(self.visited) >= self.max_pages:
                self.should_stop = True
                print("Reached maximum number of pages to crawl.")
                return False
            self.visited.add(normalized_url)
            return True

    async def get_html(self, url: str) -> str | None:
        if self.session is None:
            return
        try:
            async with self.session.get(
                url, headers={"User-Agent": "BootCrawler/1.0"}
            ) as response:
                if response.status > 399:
                    raise Exception(  # noqa: TRY002
                        f"got HTTP error: {response.status} {response.reason}"
                    )

                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type:
                    raise Exception(f"got not-HTML response: {content_type}")  # noqa: TRY002

                return await response.text()
        except ClientError as e:
            raise Exception(f"network error while fetching {url}: {e}")  # noqa: TRY002

    async def crawl_page(
        self,
        current_url: str | None = None,
    ) -> None:
        if self.should_stop:
            return

        if current_url is None:
            current_url = self.base_url

        current_url_obj = urlsplit(current_url)
        if current_url_obj.netloc != self.base_domain:
            return

        normalized_url = normalize_url(current_url)
        if not await self.add_page_visit(normalized_url):
            return

        async with self.semaphore:
            print(f"crawling of: {current_url}...")
            try:
                html = await self.get_html(current_url)
            except Exception as e:  # noqa: BLE001
                print(f"skipping {current_url}: {e}")
                return
            if html is None:
                return
            page_info = extract_page_data(html, current_url)

        async with self.lock:
            self.page_data[normalized_url] = page_info

        links = page_info["outgoing_links"]
        if links is None:
            return
        tasks = [asyncio.create_task(self.crawl_page(link)) for link in links]
        try:
            self.all_tasks.update(tasks)
            _ = await asyncio.gather(*tasks, return_exceptions=True)
        finally:
            self.all_tasks.difference_update(tasks)

    async def crawl(self) -> dict[str, PageData]:
        await self.crawl_page(self.base_url)
        return self.page_data


def normalize_url(url: str) -> str:
    parsed = urlsplit(url)
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    return netloc + path


def get_heading_from_html(html: str) -> str:
    """
    Return the content of the first h1 tag,
    fallback to the content of the first h2 tag,
    otherwise return an empty string
    """
    soup = BeautifulSoup(html, "html.parser")
    h_tag = soup.find("h1") or soup.find("h2")
    return h_tag.get_text(strip=True) if isinstance(h_tag, Tag) else ""


def get_first_paragraph_from_html(html: str) -> str:
    """
    Return the content of the first p tag in the main section,
    fallback to the content of first p tag from html,
    otherwise return an empty string
    """
    soup = BeautifulSoup(html, "html.parser")

    main_section = soup.find("main")
    if isinstance(main_section, Tag):
        first_p = main_section.find("p")
    else:
        first_p = soup.find("p")

    return first_p.get_text(strip=True) if isinstance(first_p, Tag) else ""


def get_urls_from_html(html: str, base_url: str) -> list[str] | None:
    urls: list[str] = []
    soup = BeautifulSoup(html, "html.parser")
    anchors = soup.find_all("a")

    for anchor in anchors:
        if not isinstance(anchor, Tag):
            continue
        href = anchor.get("href")
        if isinstance(href, str) and href:
            try:
                absolute_url = urljoin(base_url, href)
                urls.append(absolute_url)
            except Exception as e:  # noqa: BLE001
                print(f"{e!s}: {href}")

    return urls


def get_images_from_html(html: str, base_url: str) -> list[str] | None:
    image_urls: list[str] = []
    soup = BeautifulSoup(html, "html.parser")
    images = soup.find_all("img")

    for img in images:
        if not isinstance(img, Tag):
            continue
        src = img.get("src")
        if isinstance(src, str) and src:
            try:
                absolute_url = urljoin(base_url, src)
                image_urls.append(absolute_url)
            except Exception as e:  # noqa: BLE001
                print(f"{e!s}: {src}")

    return image_urls


def extract_page_data(html: str, page_url: str) -> PageData:
    return PageData(
        url=page_url,
        heading=get_heading_from_html(html),
        first_paragraph=get_first_paragraph_from_html(html),
        outgoing_links=get_urls_from_html(html, page_url),
        image_urls=get_images_from_html(html, page_url),
    )


async def crawl_site_async(
    base_url: str, max_concurrency: int, max_pages: int
) -> dict[str, PageData]:
    async with AsyncCrawler(base_url, max_concurrency, max_pages) as crawler:
        return await crawler.crawl()
