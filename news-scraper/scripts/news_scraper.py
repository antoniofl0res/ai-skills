import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
import json
import re
import datetime
import email.utils
import argparse
import time
import sys
import os

def decode_google_news_url(article_id):
    """
    Decodes an obfuscated Google News article ID by first extracting the signature
    and timestamp from the articles page, then using the batchexecute RPC endpoint.
    Returns the original destination URL or None if decoding fails.
    """
    url = f"https://news.google.com/articles/{article_id}"
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
            
            sig_match = re.search(r'data-n-a-sg=["\']([^"\']+)["\']', html)
            ts_match = re.search(r'data-n-a-ts=["\']([^"\']+)["\']', html)
            
            sig = sig_match.group(1) if sig_match else None
            ts = ts_match.group(1) if ts_match else None
            
            if not sig or not ts:
                return None
                
            # Request original URL via batchexecute
            articles_reqs = [
                [
                    "Fbv4je", 
                    f'["garturlreq",[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],"X","X",1,[1,1,1],1,1,null,0,0,null,0],"{article_id}","{ts}","{sig}"]',
                ]
            ]
            
            payload = f"f.req={urllib.parse.quote(json.dumps([articles_reqs]))}"
            headers = {
                "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            post_req = urllib.request.Request(
                "https://news.google.com/_/DotsSplashUi/data/batchexecute",
                data=payload.encode('utf-8'),
                headers=headers,
                method='POST'
            )
            
            with urllib.request.urlopen(post_req, timeout=10) as post_response:
                text = post_response.read().decode('utf-8')
                lines = text.split("\n")
                for line in lines:
                    if "Fbv4je" in line:
                        data = json.loads(line)
                        nested_json_str = data[0][2]
                        nested_data = json.loads(nested_json_str)
                        return nested_data[1]
    except Exception:
        pass
    return None

def fetch_meta_description(url):
    """
    Fetches the given webpage and extracts its meta description using regular expressions.
    """
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    try:
        # Fetch only the first 100KB to save bandwidth and speed up parsing
        with urllib.request.urlopen(req, timeout=5) as response:
            html_bytes = response.read(102400)
            try:
                html_str = html_bytes.decode('utf-8', errors='ignore')
            except Exception:
                html_str = html_bytes.decode('latin-1', errors='ignore')
            
            # Capture the content attribute value using a backreference to the
            # SAME opening quote character, so a description that contains the
            # other quote (e.g. content="She said 'hi'") is not truncated at the
            # inner apostrophe. Delimiter may be " or '.
            def _content_after(attr_match):
                # find content=(["'])(.*?)\1 anywhere inside this <meta ...> tag
                tag = attr_match.group(0)
                cm = re.search(r'content=(["\'])(.*?)\1', tag, re.IGNORECASE | re.DOTALL)
                return cm.group(2) if cm else None

            # Find the whole <meta ...> tag whose name/property identifies the
            # description we want, then extract its content value with matched
            # delimiters. Prefer og:description, then name=description.
            m2 = None
            for tag_m in re.finditer(r'<meta\b[^>]*>', html_str, re.IGNORECASE):
                tag = tag_m.group(0)
                if re.search(r'(?:property|name)\s*=\s*["\']og:description["\']', tag, re.IGNORECASE):
                    val = _content_after(tag_m)
                    if val is not None:
                        m2 = val
                        break
            m1 = None
            if not m2:
                for tag_m in re.finditer(r'<meta\b[^>]*>', html_str, re.IGNORECASE):
                    tag = tag_m.group(0)
                    if re.search(r'name\s*=\s*["\']description["\']', tag, re.IGNORECASE):
                        val = _content_after(tag_m)
                        if val is not None:
                            m1 = val
                            break
                
            desc = None
            if m2:
                desc = m2
            elif m1:
                desc = m1
                
            if desc:
                # Clean up html entities and whitespace
                desc = re.sub(r'\s+', ' ', desc).strip()
                desc = html_unescape(desc)
                return desc
    except Exception:
        pass
    return None

def html_unescape(s):
    """
    Simple unescaper for standard HTML entities.
    """
    s = s.replace('&quot;', '"').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    s = s.replace('&#39;', "'").replace('&apos;', "'").replace('&nbsp;', ' ')
    # Hex/decimal character entities
    s = re.sub(r'&#(\d+);', lambda m: chr(int(m.group(1))), s)
    s = re.sub(r'&#x([a-fA-F0-9]+);', lambda m: chr(int(m.group(1), 16)), s)
    return s

def fetch_news_api(query, api_key, limit=10, days=7):
    """
    Fetches news from the News API everything endpoint.
    """
    from_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    url_params = urllib.parse.urlencode({
        'q': query,
        'from': from_date,
        'sortBy': 'publishedAt',
        'pageSize': limit,
        'apiKey': api_key
    })
    url = f"https://newsapi.org/v2/everything?{url_params}"
    
    req = urllib.request.Request(
        url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            status = response.getcode()
            data = json.loads(response.read().decode('utf-8'))
            if data.get('status') == 'ok':
                articles = []
                for art in data.get('articles', []):
                    pub_date_str = art.get('publishedAt')
                    try:
                        if pub_date_str:
                            dt_str = pub_date_str.replace('Z', '+00:00')
                            pub_dt = datetime.datetime.fromisoformat(dt_str)
                        else:
                            pub_dt = datetime.datetime.now(datetime.timezone.utc)
                    except Exception:
                        pub_dt = datetime.datetime.now(datetime.timezone.utc)

                    # Coerce naive datetimes to UTC for safe downstream
                    # comparison and sorting.
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=datetime.timezone.utc)

                    articles.append({
                        'title': art.get('title', 'Untitled'),
                        'url': art.get('url', ''),
                        'pub_date': pub_dt,
                        'source': art.get('source', {}).get('name', 'Unknown'),
                        'description': art.get('description') or 'Description not available.',
                        'engine': 'News API'
                    })
                return articles
            else:
                print(f"News API error (HTTP {status}): {data.get('message', 'Unknown error')}", file=sys.stderr)
    except urllib.error.HTTPError as he:
        # Surface the HTTP status so a 429 rate limit, 401 bad key, or 5xx
        # server error is distinguishable from a genuine empty result.
        body = ''
        try:
            body = he.read().decode('utf-8', errors='ignore')[:200]
        except Exception:
            pass
        print(f"News API HTTP {he.code} error: {body or he.reason}", file=sys.stderr)
    except Exception as e:
        print(f"Error fetching from News API: {e}", file=sys.stderr)
    return []

def normalize_url(url):
    """
    Normalizes a URL to assist in deduplication.
    """
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url.lower())
        netloc = parsed.netloc
        if netloc.startswith("www."):
            netloc = netloc[4:]
        path = parsed.path.rstrip('/')
        return f"{netloc}{path}"
    except Exception:
        return url.lower()

def scrape_news(query, limit=10, days=7, detailed=False, source="google", api_key=None):
    """
    Searches Google News RSS and/or News API, deduplicates, and formats output.
    """
    google_articles = []
    newsapi_articles = []
    
    # 1. Fetch Google Articles
    if source in ["google", "both"]:
        search_query = f"{query} when:{days}d"
        encoded_query = urllib.parse.quote(search_query)
        rss_url = f"https://news.google.com/rss/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
        
        req = urllib.request.Request(
            rss_url,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        print(f"Searching Google News RSS for: '{search_query}'...", file=sys.stderr)
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()
                root = ET.fromstring(xml_data)
                items = root.findall('.//item')
                print(f"Found {len(items)} raw RSS entries.", file=sys.stderr)
                
                cutoff_date = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=days)
                
                for item in items:
                    title = item.find('title').text
                    link = item.find('link').text
                    pub_date_str = item.find('pubDate').text
                    src_name = item.find('source').text if item.find('source') is not None else "Unknown"
                    
                    try:
                        pub_dt = email.utils.parsedate_to_datetime(pub_date_str)
                    except Exception:
                        pub_dt = datetime.datetime.now(datetime.timezone.utc)

                    # parsedate_to_datetime can return a naive datetime when the
                    # pubDate string lacks a TZ offset; coerce to UTC so the
                    # comparison against the aware cutoff_date cannot raise
                    # TypeError on a malformed item.
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=datetime.timezone.utc)

                    if pub_dt < cutoff_date:
                        continue
                        
                    match = re.search(r'(?:rss/articles|articles|read)/([^?#]+)', link)
                    article_id = match.group(1) if match else None
                    # Normalize to /articles/ form so it redirects in browsers
                    clean_link = f"https://news.google.com/articles/{article_id}" if article_id else link

                    google_articles.append({
                        'title': title,
                        'google_link': clean_link,
                        'article_id': article_id,
                        'pub_date': pub_dt,
                        'source': src_name,
                        'engine': 'Google News'
                    })
        except Exception as e:
            print(f"Error fetching Google News RSS: {e}", file=sys.stderr)

    # 2. Fetch News API Articles
    newsapi_used = False
    if source in ["newsapi", "both"]:
        if not api_key:
            print("Warning: News API requested but no API key provided. Skipping News API.", file=sys.stderr)
        else:
            print(f"Searching News API for: '{query}'...", file=sys.stderr)
            newsapi_articles = fetch_news_api(query, api_key, limit=limit * 2, days=days)
            print(f"Found {len(newsapi_articles)} entries from News API.", file=sys.stderr)
            newsapi_used = bool(newsapi_articles)
            
    # If source was only newsapi but failed to run because of no key
    if source == "newsapi" and not api_key:
        print("Falling back to Google News RSS because News API key is missing.", file=sys.stderr)
        return scrape_news(query, limit, days, detailed, "google")

    # 3. Merge & Deduplicate
    merged = []
    seen_urls = {}

    def _title_key(t):
        return re.sub(r'[^a-zA-Z0-9]', '', t.lower())

    def _day_key(dt):
        return dt.astimezone(datetime.timezone.utc).date()

    # We process News API articles first because they already have direct URLs and summaries
    for art in newsapi_articles:
        norm = normalize_url(art['url'])
        seen_urls[norm] = art
        merged.append(art)

    # We process Google articles. Suppress a Google item only when it is a
    # strong duplicate of an already-merged article: same publication day AND a
    # near-identical title (one normalized title contains the other AND the
    # shorter one is at least 60% of the longer one's length, so short generic
    # titles like "Update" no longer suppress distinct follow-ups).
    for art in google_articles:
        norm = normalize_url(art.get('google_link', ''))
        if norm and norm in seen_urls:
            continue
        norm_title = _title_key(art['title'])
        art_day = _day_key(art['pub_date'])
        is_dup = False
        for seen in merged:
            seen_title = _title_key(seen['title'])
            if not seen_title or not norm_title:
                continue
            shorter, longer = sorted([seen_title, norm_title], key=len)
            same_day = (_day_key(seen['pub_date']) == art_day)
            contains = longer.startswith(shorter) or shorter in longer
            length_ratio = len(shorter) / len(longer) if longer else 0
            if same_day and contains and length_ratio >= 0.6:
                is_dup = True
                break

        if is_dup:
            continue

        if norm:
            seen_urls[norm] = art
        merged.append(art)

    # Sort merged list by publication date descending; tiebreak on title for a
    # stable, deterministic order regardless of insertion sequence.
    merged.sort(key=lambda x: (x['pub_date'], _title_key(x['title'])), reverse=True)
    
    # Limit merged list
    selected = merged[:limit]
    
    # 4. Resolve details for selected Google articles (if detailed)
    processed_articles = []
    for i, art in enumerate(selected):
        if art.get('engine') == 'Google News':
            print(f"Processing Google article {i+1}/{len(selected)}: {art['title'][:40]}...", file=sys.stderr)
            decoded_url = art['google_link']
            description = "Description not fetched."
            
            if detailed and art.get('article_id'):
                decoded_url = decode_google_news_url(art['article_id'])
                if decoded_url:
                    time.sleep(1.0)
                    desc = fetch_meta_description(decoded_url)
                    description = desc if desc else "Description not available."
                else:
                    decoded_url = art['google_link']
                    description = "Could not resolve original URL."
            
            clean_title = art['title']
            source_suffix = f" - {art['source']}"
            if clean_title.endswith(source_suffix):
                clean_title = clean_title[:-len(source_suffix)]
                
            processed_articles.append({
                'title': clean_title,
                'url': decoded_url,
                'pub_date': art['pub_date'],
                'source': art['source'],
                'description': description,
                'engine': 'Google News'
            })
        else:
            # Already resolved News API article
            processed_articles.append(art)
            
    # 5. Format Output
    today_str = datetime.datetime.now().strftime("%d %B %Y")
    
    md = []
    md.append(f"# {query.upper()} NEWS DIGEST")
    md.append(f"### TOPIC: {query.upper()} | LAST {days} DAYS")
    md.append(f"**Compiled:** {today_str} | **Coverage window:** {(datetime.datetime.now() - datetime.timedelta(days=days)).strftime('%d %B %Y')} to {today_str}")
    md.append("")
    md.append("---")
    md.append("")
    md.append("## EXECUTIVE SUMMARY")
    md.append(f"– Generated automated news roundup for query: \"{query}\".")
    md.append(f"– Source engine: {source.upper()} (News API key used: {'Yes' if newsapi_used else 'No'}).")
    md.append(f"– Retrieved {len(processed_articles)} unique articles from the last {days} days.")
    md.append("")
    md.append("## NEWS ARTICLES")
    md.append("")

    for i, art in enumerate(processed_articles):
        date_str = art['pub_date'].strftime("%d %B %Y")
        md.append(f"### {i+1}. [{art['title']}]({art['url']})")
        md.append("")
        md.append(f"– **Source:** {art['source']} (via {art['engine']})")
        md.append(f"– **Published:** {date_str}")
        # The article title above is itself a clickable hyperlink to the URL,
        # so a redundant "Link:" bullet is omitted to keep the report concise.

        if art['description'] and art['description'] != "Description not fetched.":
            clean_desc = re.sub(r'\s+', ' ', art['description']).strip()
            clean_desc = clean_desc.replace('—', ';')
            md.append(f"– **Summary:** {clean_desc}")
        md.append("")

    md.append("---")
    md.append("*Disclaimer: Retrieved via automated script. Publication dates reflect RSS/API metadata; original publisher sources should be verified before citation. For professional reference only.*")
    
    return "\n".join(md)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape news from Google News RSS and/or News API based on a topic.")
    parser.add_argument("--query", "-q", required=True, help="Search query or topic")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Max articles to fetch (default: 10)")
    parser.add_argument("--days", "-d", type=int, default=7, help="Date range in days (default: 7)")
    parser.add_argument("--detailed", action="store_true", help="Resolve Google News links and fetch meta descriptions")
    parser.add_argument("--source", choices=["google", "newsapi", "both"], default="both", help="News source engine (default: both)")
    parser.add_argument("--api-key", help="News API key (can also be set via NEWS_API_KEY env var)")
    parser.add_argument("--output", "-o", help="File path to save the Markdown report")
    
    args = parser.parse_args()
    
    # Try to load variables from local .env file in the current directory
    if os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ[k.strip()] = v.strip().strip('"').strip("'")
        except Exception:
            pass
            
    # Resolve API Key
    api_key = args.api_key or os.environ.get("NEWS_API_KEY")
    
    report = scrape_news(
        args.query, 
        limit=args.limit, 
        days=args.days, 
        detailed=args.detailed, 
        source=args.source, 
        api_key=api_key
    )
    
    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(report)
            print(f"Successfully wrote report to {args.output}", file=sys.stderr)
        except Exception as e:
            print(f"Error writing output file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(report)
