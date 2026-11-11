"""Bounded HTTPS fetches pinned to validated public IPs; no proxy or private-network access."""

import http.client
import ipaddress
import socket
import ssl
import time
from urllib.parse import urlsplit, urljoin
from urllib.robotparser import RobotFileParser

AGENT = "NorthGeorgiaHolidayEventsBot/1.0 (+https://github.com/wjdecorte/christmas)"
MAX_BODY = 2_000_000


def validate_url(url):
    p = urlsplit(url)
    if (
        p.scheme != "https"
        or not p.hostname
        or p.username
        or p.password
        or p.port not in (None, 443)
    ):
        raise ValueError(
            "Sources must use HTTPS on port 443 without embedded credentials"
        )
    if len(url) > 2000 or any(ord(c) < 33 for c in url):
        raise ValueError("Invalid source URL")
    try:
        if not ipaddress.ip_address(p.hostname).is_global:
            raise ValueError("Private, loopback and reserved addresses are not allowed")
    except ValueError as exc:
        if "not allowed" in str(exc):
            raise
        # A normal DNS name is resolved and checked immediately before connecting.
        if p.hostname.lower() in ("localhost",) or "." not in p.hostname:
            raise ValueError("A public source hostname is required")
    return p


class PublicHTTPS(http.client.HTTPSConnection):
    def connect(self):
        addresses = socket.getaddrinfo(self.host, self.port, type=socket.SOCK_STREAM)
        if not addresses or any(
            not ipaddress.ip_address(a[4][0]).is_global for a in addresses
        ):
            raise ValueError("Source resolved to a non-public address")
        # Connect to the checked numeric address, retaining original TLS SNI/certificate validation.
        family, socktype, proto, _, target = addresses[0]
        sock = socket.socket(family, socktype, proto)
        sock.settimeout(self.timeout)
        try:
            sock.connect(target)
            self.sock = self._context.wrap_socket(sock, server_hostname=self.host)
        except BaseException:
            sock.close()
            raise


def fetch(url, host, limit=MAX_BODY):
    for _ in range(4):
        p = validate_url(url)
        if p.hostname.lower() != host.lower():
            raise ValueError(
                "Cross-host redirects are not followed; update the approved source URL"
            )
        conn = PublicHTTPS(
            p.hostname, 443, timeout=12, context=ssl.create_default_context()
        )
        try:
            path = p.path or "/"
            if p.query:
                path += "?" + p.query
            conn.request(
                "GET",
                path,
                headers={
                    "User-Agent": AGENT,
                    "Accept": "text/html, text/calendar, application/ld+json, application/json;q=0.9",
                    "Accept-Encoding": "identity",
                },
            )
            r = conn.getresponse()
            if r.status in (301, 302, 303, 307, 308):
                url = urljoin(url, r.getheader("Location", ""))
                continue
            if r.status in (404, 410):
                return r.status, "", url
            if r.status != 200:
                raise ValueError(f"Source returned HTTP {r.status}; no events changed")
            if r.getheader("Content-Encoding", "identity").lower() not in (
                "identity",
                "",
            ):
                raise ValueError(
                    "Compressed source response is unsupported; no events changed"
                )
            chunks = []
            size = 0
            deadline = time.monotonic() + 25
            while True:
                chunk = r.read1(min(65536, limit + 1 - size))
                if not chunk:
                    break
                size += len(chunk)
                chunks.append(chunk)
                if size > limit:
                    raise ValueError("Source exceeded the response-size limit")
                if time.monotonic() > deadline:
                    raise ValueError("Source response deadline exceeded")
            body = b"".join(chunks)
            return r.status, body.decode("utf-8", errors="replace"), url
        finally:
            conn.close()
    raise ValueError("Too many source redirects")


class PoliteReader:
    def __init__(self, url, stop=None):
        self.host = validate_url(url).hostname
        self.stop = stop
        self.last = 0.0
        self.delay = 1.1
        self.robots = None

    def get(self, url):
        p = validate_url(url)
        if p.hostname.lower() != self.host.lower():
            raise ValueError("Only the approved source host can be fetched")
        if self.robots is None:
            self.robots = RobotFileParser()
            status, text, _ = fetch(
                f"https://{self.host}/robots.txt", self.host, 200_000
            )
            self.robots.parse(text.splitlines() if status == 200 else [])
            delay = (
                self.robots.crawl_delay(AGENT) or self.robots.crawl_delay("*") or 1.1
            )
            if delay > 30:
                raise ValueError(
                    "Source requests a long crawl delay; use its calendar feed instead"
                )
            self.delay = max(1.1, float(delay))
            self.last = time.monotonic()
        if not self.robots.can_fetch(AGENT, url):
            raise ValueError("robots.txt does not allow this page; no events changed")
        remaining = max(0, self.delay - (time.monotonic() - self.last))
        if self.stop:
            if self.stop.wait(remaining):
                raise ValueError("Source check interrupted")
        else:
            time.sleep(remaining)
        result = fetch(url, self.host)
        self.last = time.monotonic()
        return result
