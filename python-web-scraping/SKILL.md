---
name: python-web-scraping
description: >-
  Pre-flight gates and routing rules for web scraping with Python. Use whenever the user asks to
  scrape, crawl, extract, or monitor data from a website or saved HTML — even casually ("pull the
  prices from this page", "get all the listings into a CSV"). Enforces robots.txt compliance,
  polite fetch discipline, and the static-HTML vs JSON-API vs JavaScript-rendering routing decision.
---

# Python web scraping — gates and routing

You already know BeautifulSoup syntax. This skill exists because a few critical steps are
reliably skipped under default operation. Follow them in order.

## 1. Pre-flight gate (before the first fetch)

Check robots.txt and honor it — `Disallow` means abstain, `Crawl-delay` means wait that long
between requests:

```python
from urllib.robotparser import RobotFileParser
rp = RobotFileParser()
rp.set_url(f"{base_url}/robots.txt")
rp.read()
if not rp.can_fetch("*", target_url):
    # Stop. Report to the user that robots.txt disallows this path — do not scrape it.
```

Also consider: the site's terms of service, copyright on the data, and personal data (GDPR).
Identify yourself with a descriptive User-Agent so operators can contact you.

## 2. Route before you parse

Look at what the page actually is before reaching for BeautifulSoup:

- **Data already served as JSON?** Check the browser Network tab (or fetch the page and look for
  `fetch`/XHR calls in its scripts). If the site loads data from a JSON endpoint, request that
  endpoint directly — it's faster and far less fragile than parsing the DOM.
- **Content rendered by JavaScript?** If the raw HTML from `requests` lacks the data you can see
  in the browser (e.g. an empty `<div id="app">`), `requests` + BeautifulSoup cannot get it.
  Use **Playwright** or **Selenium**. (Scrapy is NOT a JavaScript renderer — it's an HTTP
  framework; it only renders JS when paired with Splash or a headless-browser middleware.)
- **Plain static HTML?** requests + BeautifulSoup (`lxml` parser if installed, else
  `'html.parser'` — it's a fine pure-Python fallback).

## 3. Fetch discipline

```python
import time, requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0 (compatible; MyScraper/1.0; contact@example.com)"
session.mount("https://", HTTPAdapter(max_retries=Retry(
    total=3, backoff_factor=0.5, status_forcelist=[429, 500, 502, 503, 504])))

resp = session.get(url, timeout=30)
resp.raise_for_status()          # never parse a failed response
# ... parse ...
time.sleep(1)                    # be polite: delay between successive page requests
```

Never use a bare `except Exception` that swallows the traceback — catch specific request
exceptions and let programming errors surface.

## 4. Robustness rules

- **No unguarded dot-chains.** `job.header.h2.a` raises `AttributeError` the first time any link
  in the chain is missing. Use `.find()`/`.select_one()` and check for `None`; skip or blank the
  field for incomplete items instead of crashing the run.
- **Create output directories** before path-templated writes: `os.makedirs(d, exist_ok=True)`.
- **Normalize whitespace** with `re.sub(r'\s+', ' ', text).strip()` — `.replace(' ', '')` only
  removes literal spaces, not tabs/newlines/non-breaking spaces.
- **CSV export**: `open(path, 'w', newline='', encoding='utf-8')`.
- **Proxies and credentials** come from environment variables, never hardcoded. Don't use free
  public proxies — they can log or tamper with your traffic.
- **During development**, fetch once and save the HTML locally; iterate on the saved file.
- **No `while True` polling loops** without `try/except KeyboardInterrupt` for graceful shutdown —
  and prefer an OS scheduler (cron/Task Scheduler) over a sleeping process.
