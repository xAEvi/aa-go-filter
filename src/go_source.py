"""Fetch and parse the Opencode Go model lineup."""

import re
import socket
import urllib.parse
import urllib.request

GO_PAGE_URL = "https://opencode.ai/go"

# IPv6 connects to opencode.ai can stall for 20-40s on some networks and
# Python has no happy eyeballs fallback, so try IPv4 addresses first.
_getaddrinfo = socket.getaddrinfo


def _getaddrinfo_ipv4_first(*args, **kwargs):
    infos = _getaddrinfo(*args, **kwargs)
    return sorted(infos, key=lambda info: info[0] != socket.AF_INET)


socket.getaddrinfo = _getaddrinfo_ipv4_first

# One entry of the goModels array: {id: "...", name: "...", requests: ...}.
# Keys may be bare (dev build) or quoted (minified JSON-style).
MODEL_RE = re.compile(
    r'\{\s*"?id"?\s*:\s*"[^"]+"\s*,\s*"?name"?\s*:\s*"([^"]+)"\s*,\s*"?requests"?\s*:'
)


def fetch_bytes(url, timeout=60):
    # Fetch a URL with a browser user agent.
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return res.read()


def parse_asset_urls(html, base=GO_PAGE_URL):
    # Collect the hashed JS bundles referenced by the Go page.
    # The route bundle (index-*.js) holds goModels, so it goes first.
    paths = list(dict.fromkeys(
        re.findall(r'(?:href|src)="(/_build/assets/[^"]+\.js)"', html)
    ))
    paths.sort(key=lambda p: not p.rsplit("/", 1)[-1].startswith("index-"))
    return [urllib.parse.urljoin(base, p) for p in paths]


def parse_go_models(js):
    # Take the name of every Go model entry in a JS bundle.
    names = [re.sub(r"\s+", " ", n).strip() for n in MODEL_RE.findall(js)]
    return list(dict.fromkeys(n for n in names if n))


def fetch_go_models():
    # The /go page only renders the featured rows; the full lineup
    # lives in the goModels array of one of its JS bundles.
    html = fetch_bytes(GO_PAGE_URL).decode("utf-8", errors="ignore")
    assets = parse_asset_urls(html)
    if not assets:
        raise RuntimeError("No JS bundles found on the Go page.")

    for url in assets:
        # Some unrelated bundles are slow on the CDN; skip instead of waiting.
        try:
            js = fetch_bytes(url, timeout=15).decode("utf-8", errors="ignore")
        except OSError:
            continue
        names = parse_go_models(js)
        if names:
            return names
    raise RuntimeError("Go model list not found in any Go page bundle.")
