---
name: news-scraper
description: >-
  Scrape news from the internet based on a theme, topic, or query. Supports
  Google News RSS and News API with automatic merging and deduplication. Returns
  formatted markdown conforming to the professional style guide.
---

# News Scraper Skill

Use this skill to fetch, parse, and summarize recent news articles from the internet on any topic.

## Usage Protocol

To scrape news, invoke the Python command-line utility. Run the script using the following command structure:

```powershell
python "C:\Users\Antonio Flores\.gemini\config\skills\news-scraper\scripts\news_scraper.py" --query "<search_topic>" [--source <google|newsapi|both>] [--api-key "<news_api_key>"] [--days <days>] [--limit <limit>] [--detailed] [--output "<output_path>"]
```

### CLI Parameters

– `--query` / `-q` (Required): The search string or topic (e.g. `"HIV prevention"`, `"AI workshop"`).
– `--source` (Optional): The news source engine to use. Choices: `google`, `newsapi`, `both`. Defaults to `both`.
– `--api-key` (Optional): News API key. If omitted, the script checks the `NEWS_API_KEY` environment variable.
– `--days` / `-d` (Optional): The number of days of history to cover. Defaults to `7`.
– `--limit` / `-l` (Optional): The maximum number of articles to return. Defaults to `10`.
– `--detailed` (Optional): If passed, the script will resolve Google News redirect URLs to original publisher URLs, and scrape webpage meta descriptions to produce article summaries. This adds a 1-second delay per article.
– `--output` / `-o` (Optional): Path to write the Markdown report. If omitted, prints to standard output.

### Style and Formatting Rules

The output report will follow these rules:
1. **Case**: Main titles and section headings are in UPPERCASE.
2. **Bullets**: List items use the en-dash (–) character.
3. **No Em-Dashes**: Em-dashes (—) are prohibited; colons or semicolons are used instead.
4. **Tone**: Factual, evidence-based, and objective.
