import ipaddress
import re
import socket
from html import unescape
from html.parser import HTMLParser
from urllib.error import URLError, HTTPError
from urllib.parse import urlparse, urlunparse
from urllib.request import Request, urlopen

from pypdf import PdfReader

from config import (
    WEB_MAX_CONTENT_BYTES,
    WEB_REQUEST_TIMEOUT_SECONDS,
    WEB_USER_AGENT,
)


class _VisibleTextHTMLParser(HTMLParser):
    def __init__(self):
        """Initialize parser state for visible text and title extraction."""
        super().__init__()
        self._ignored_depth = 0
        self._in_title = False
        self._parts = []
        self.title = ""

    def handle_starttag(self, tag, attrs):
        """Track tags that should be ignored and enter title mode."""
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1
        elif tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        """Leave ignored/title sections when closing tags are reached."""
        if tag in {"script", "style", "noscript"} and self._ignored_depth > 0:
            self._ignored_depth -= 1
        elif tag == "title":
            self._in_title = False

    def handle_data(self, data):
        """Collect cleaned visible text and store the first title value."""
        if not data or self._ignored_depth > 0:
            return

        cleaned = " ".join(data.split())
        if not cleaned:
            return

        if self._in_title and not self.title:
            self.title = cleaned

        self._parts.append(cleaned)

    def extract_text(self) -> str:
        """Return all collected visible text joined by newlines."""
        return "\n".join(self._parts)


def extract_text_from_file(file_path: str) -> str:
    """Extract plain text from supported local files (TXT, PDF)."""
    lower_path = file_path.lower()

    if lower_path.endswith(".txt"):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()

    if lower_path.endswith(".pdf"):
        reader = PdfReader(file_path)
        text_parts = []

        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        return "\n\n".join(text_parts)

    raise ValueError("Nur TXT- und PDF-Dateien werden unterstützt.")


def normalize_and_validate_url(raw_url: str) -> str:
    """Normalize a URL and reject unsupported or unsafe targets."""
    if not raw_url or not raw_url.strip():
        raise ValueError("Bitte eine URL eingeben.")

    url = raw_url.strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        url = "https://" + url

    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Nur http- und https-URLs werden unterstützt.")

    if not parsed.hostname:
        raise ValueError("Ungültige URL: Hostname fehlt.")

    _assert_public_host(parsed.hostname)

    normalized = urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path or "/", "", parsed.query, "")
    )

    return normalized


def extract_text_from_url(raw_url: str) -> dict:
    """Download a public URL and return normalized URL, title, and text."""
    normalized_url = normalize_and_validate_url(raw_url)

    request = Request(
        normalized_url,
        headers={
            "User-Agent": WEB_USER_AGENT,
            "Accept": "text/html,text/plain;q=0.9,*/*;q=0.5",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=WEB_REQUEST_TIMEOUT_SECONDS) as response:
            content_type = (response.headers.get("Content-Type") or "").lower()
            charset = response.headers.get_content_charset() or "utf-8"
            payload = response.read(WEB_MAX_CONTENT_BYTES + 1)
    except HTTPError as exc:
        raise ValueError(f"URL konnte nicht geladen werden (HTTP {exc.code}).") from exc
    except URLError as exc:
        raise ValueError(f"URL konnte nicht geladen werden: {exc.reason}") from exc

    if len(payload) > WEB_MAX_CONTENT_BYTES:
        raise ValueError("Die Seite ist zu groß zum Indexieren (Limit überschritten).")

    body = payload.decode(charset, errors="ignore")

    if "text/plain" in content_type:
        text = _normalize_text(body)
        title = _title_from_url(normalized_url)
    else:
        parser = _VisibleTextHTMLParser()
        parser.feed(body)
        parser.close()
        text = _normalize_text(parser.extract_text())
        title = parser.title or _title_from_url(normalized_url)

    if not text:
        raise ValueError("Auf der URL wurde kein lesbarer Text gefunden.")

    return {
        "normalized_url": normalized_url,
        "title": title,
        "text": text,
    }


def _assert_public_host(hostname: str) -> None:
    """Block localhost, private, and non-global IP targets."""
    lowered = hostname.lower()

    if lowered in {"localhost", "localhost.localdomain"}:
        raise ValueError("Lokale Hosts sind nicht erlaubt.")

    try:
        literal_ip = ipaddress.ip_address(lowered)
    except ValueError:
        literal_ip = None

    if literal_ip is not None:
        if not literal_ip.is_global:
            raise ValueError("Private oder lokale IP-Adressen sind nicht erlaubt.")
        return

    if literal_ip is None:
        try:
            addr_info = socket.getaddrinfo(hostname, None)
        except socket.gaierror as exc:
            raise ValueError("Hostname konnte nicht aufgelöst werden.") from exc

        for entry in addr_info:
            ip_str = entry[4][0]
            try:
                ip_obj = ipaddress.ip_address(ip_str)
            except ValueError:
                continue
            if not ip_obj.is_global:
                raise ValueError(
                    "URL zeigt auf ein privates oder lokales Netzwerkziel."
                )


def _normalize_text(text: str) -> str:
    """Unescape HTML and collapse whitespace into clean lines."""
    unescaped = unescape(text)
    lines = [" ".join(line.split()) for line in unescaped.splitlines()]
    filtered = [line for line in lines if line]
    return "\n".join(filtered).strip()


def _title_from_url(normalized_url: str) -> str:
    """Derive a fallback title from the URL path or hostname."""
    parsed = urlparse(normalized_url)
    path_segment = parsed.path.rstrip("/").split("/")[-1]
    return path_segment or parsed.hostname or normalized_url
