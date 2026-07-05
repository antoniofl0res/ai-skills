---
name: python-web-scraping
description: >-
  Perform web scraping using Python, BeautifulSoup, and Requests. Covers parsing local/remote HTML,
  dot-navigation and tag-chaining, text cleaning, data export, interactive filtering, and scheduled loops.
---

# Python Web Scraping Guidelines

A guide to programmatically extracting structured data from web pages using Python, `Requests`, and `BeautifulSoup`. 

---

## 1. Core Architecture & Browser Workflow

Web scraping involves retrieving a web document and parsing its structure to extract data. Before writing code, use the browser developer tools to inspect the target page:
* **The "Inspect" Workflow**: Right-click on any element on the page (e.g., a book title, a price, or a job card) and select **Inspect**.
* **Identify Patterns**: Look for recurring structures. For example, if every book is wrapped in a `<div class="product_pod">` or every job is inside an `<li class="clearfix job-bx">`, that class name is the unique "magnet" you will target.

---

## 2. Setup & Parser Selection

Install the core libraries in your environment:
```bash
pip install requests beautifulsoup4 lxml
```

### Parser Selection: Why `lxml`?
Always prefer `lxml` as the parsing engine over the default `html.parser`. It is written in C, making it significantly faster, and it is highly resilient when parsing broken or malformed HTML documents.

### Standard Import Header
Always include the following imports at the top of your scraping script:
```python
from bs4 import BeautifulSoup
import requests
import csv
import time
```

---

## 3. Local File Parsing (Development & Testing)

During development, save the HTML page locally to avoid making repetitive network requests and triggering rate limits.

```python
# Read a local HTML file
with open('home.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Initialize BeautifulSoup with the lxml parser
soup = BeautifulSoup(content, 'lxml')

# Prettify for debugging/inspection of the parsed structure
print(soup.prettify())
```

---

## 4. Remote Page Fetching

To fetch live HTML, use `requests.get()`. Always inspect the HTTP response status code to handle blocks:
```python
url = "https://books.toscrape.com"
response = requests.get(url)

# Status Code Validation
if response.status_code == 200:
    print("Successfully connected.")
    html_text = response.text
elif response.status_code == 403:
    print("Access Denied (403 Forbidden). IP block or user-agent restriction encountered.")
else:
    print(f"Failed to fetch page. Status code: {response.status_code}")
```

---

## 5. DOM Traversal & Searching

### Find vs. Find All
* **`soup.find('tag')`**: Returns the *first* matching tag object, or `None`.
* **`soup.find_all('tag')`**: Returns a *list* (ResultSet) of all matching tag objects. You **must** iterate over this list using a loop to process individual elements.

### Targeting CSS Classes
Because `class` is a reserved keyword in Python, BeautifulSoup uses **`class_`** (with an underscore) to match class attributes:
```python
# Find all course cards
cards = soup.find_all('div', class_='card')
```

### Nested Relative Searching
Instead of searching the global `soup`, query a parent tag directly to scope your search:
```python
for card in cards:
    # Searches only inside the current card element
    title_tag = card.find('h5')
```

### Tag Chaining (Dot-Navigation)
You can walk down a known HTML tree hierarchy by chaining tags:
```python
# Traverses: parent -> child header -> child h2 -> child a tag
link_tag = job.header.h2.a
```

### Attribute & Text Extraction
* **Text**: Access the inner text of a tag using `.text`.
* **Attributes**: Access attribute values (like links `href` or image sources `src`) using dictionary-style bracket notation:
```python
link = link_tag['href']
text_content = link_tag.text
```

---

## 6. Text Cleaning & Token Extraction

Scraped text is often cluttered with whitespace, tabs, and newlines. Use string methods to clean the data:
* **`.strip()`**: Removes leading and trailing whitespace.
* **`.replace(' ', '')`**: Removes all whitespace or replaces newlines (`\n`).
* **`.split()`**: Splitting text into words to extract specific tokens (e.g., getting a price from a sentence).

```python
# Clean whitespace
clean_title = title_tag.text.strip()

# Extract price from a string like "Price: $20.00"
raw_price = card.find('p', class_='price').text  # "Price: $20.00"
price = raw_price.split('$')[-1]                 # "20.00"
```

---

## 7. Interactive Filtering & Saving Output

### Interactive User Exclusion
Prompt the user for skills or keywords they want to filter out, then conditionally skip matching elements:
```python
unfamiliar_skill = input("Enter a skill you do not know: ").strip().lower()

for job in jobs:
    skills = job.find('span', class_='skills').text.lower()
    if unfamiliar_skill in skills:
        # Skip this job listing
        continue
```

### Exporting to CSV
Use Python's built-in `csv` module to save structured data directly to a spreadsheet:
```python
with open('results.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    # Write header
    writer.writerow(['Title', 'Price', 'Link'])
    
    for item in scraped_items:
        writer.writerow([item['title'], item['price'], item['link']])
```

### Exporting to Numbered Files
Use `enumerate()` to dynamically create separate text files inside a loop:
```python
for index, job in enumerate(jobs):
    with open(f'posts/{index}.txt', 'w', encoding='utf-8') as f:
        f.write(f"Company: {company}\nSkills: {skills}\n")
```

---

## 8. Scheduled Run Loops

To run a scraper periodically (e.g., polling for new job listings every 10 minutes), wrap the execution in a loop with a delay:

```python
import time

def run_scraper():
    # Scraping logic goes here...
    print("Scrape completed.")

if __name__ == '__main__':
    while True:
        run_scraper()
        # Sleep for 10 minutes (600 seconds)
        time.sleep(600)
```

---

## 9. Handling Advanced Obstacles ("The Bosses")

1. **Pagination**: Analyze how the page number changes in the URL (e.g., `page=2`). Loop through page indexes and format the URL dynamically.
2. **JavaScript Rendering**: For pages where content loads dynamically via JS, standard `Requests` cannot read it. Use dynamic browser automation tools like **Playwright** or **Scrapy**.
3. **IP Blocking & Rate Limiting**: Avoid getting banned by rotating user agents and using residential proxies (e.g., Data Impulse). Pass proxies directly to requests:
```python
proxies = {
    'http': 'http://username:password@proxy_host:port',
    'https': 'http://username:password@proxy_host:port',
}
response = requests.get(url, proxies=proxies)
```

---

## 10. Boilerplate Scraping Template

Use this template as a starting point for writing structured Python scrapers:

```python
from bs4 import BeautifulSoup
import requests
import csv
import time

def scrape_jobs(unfamiliar_skill):
    url = "https://example-jobs-site.com/search?q=python"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch data: HTTP {response.status_code}")
            return
        
        soup = BeautifulSoup(response.text, 'lxml')
        job_listings = soup.find_all('li', class_='job-listing-card')
        
        with open('scraped_jobs.csv', 'w', newline='', encoding='utf-8') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(['Company', 'Skills', 'Link'])
            
            for index, job in enumerate(job_listings):
                # Tag Chaining & Nested Searches
                company = job.header.h3.text.strip()
                skills = job.find('span', class_='job-skills').text.strip()
                link = job.header.h3.a['href']
                
                # Interactive Exclusions
                if unfamiliar_skill.lower() in skills.lower():
                    continue
                
                # CSV Export
                writer.writerow([company, skills, link])
                
                # Numbered File Export
                with open(f'posts/{index}.txt', 'w', encoding='utf-8') as text_file:
                    text_file.write(f"Company: {company}\nSkills: {skills}\nLink: {link}\n")
                    
        print("Jobs successfully scraped and saved.")
        
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == '__main__':
    unfamiliar = input("Enter skill to filter out: ").strip()
    while True:
        scrape_jobs(unfamiliar)
        print("Waiting 10 minutes for the next run...")
        time.sleep(600)
```
