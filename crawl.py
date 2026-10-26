from urllib.parse import urlsplit

from bs4 import BeautifulSoup, Tag


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
