"""Fetch and parse the Opencode Go model lineup."""

import re
import urllib.request

GO_DOCS_URL = "https://opencode.ai/docs/go/"


def fetch_bytes(url):
    # Fetch a URL with a browser user agent.
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as res:
        return res.read()


def parse_go_models(html):
    # Isolate the "current list of models includes" section first.
    section = re.search(
        r"The current list of models includes:</p>\s*<ul>(.*?)</ul>",
        html,
        re.S,
    )
    if not section:
        raise RuntimeError("Go model list section not found in docs HTML.")

    # Take the bold entry of each list item in that section only.
    names = re.findall(r"<li><strong>(.*?)</strong>", section.group(1))
    names = [re.sub(r"\s+", " ", n).strip() for n in names if n.strip()]
    if not names:
        raise RuntimeError("No Go models parsed from docs section.")
    return names


def fetch_go_models():
    # Download the Go docs page and return the model names.
    html = fetch_bytes(GO_DOCS_URL).decode("utf-8", errors="ignore")
    return parse_go_models(html)
