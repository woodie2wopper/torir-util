#!/usr/bin/env python3
"""
Google Patents scraper to extract title and abstract from patent URLs.
Supports both command-line arguments and pipe input.
"""

import sys
import argparse
import json
import re
from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup


def extract_patent_id(url):
    """Extract patent ID from Google Patents URL."""
    match = re.search(r'/patent/([^/]+)', url)
    if match:
        return match.group(1)
    return None


def scrape_patent_info(url):
    """Scrape patent title and abstract from Google Patents URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title_element = soup.find('span', {'itemprop': 'title'})
        if not title_element:
            title_element = soup.find('h1')
        title = title_element.get_text(strip=True) if title_element else "Title not found"
        
        abstract_element = soup.find('div', {'itemprop': 'abstract'})
        if not abstract_element:
            abstract_element = soup.find('section', {'itemprop': 'abstract'})
        if not abstract_element:
            abstract_element = soup.find('div', class_='abstract')
        
        abstract = abstract_element.get_text(strip=True) if abstract_element else "Abstract not found"
        
        patent_id = extract_patent_id(url)
        
        return {
            "ID": patent_id,
            "Title": title,
            "Abstract": abstract
        }
        
    except requests.RequestException as e:
        return {
            "ID": extract_patent_id(url),
            "Title": f"Error: {str(e)}",
            "Abstract": f"Error: {str(e)}"
        }
    except Exception as e:
        return {
            "ID": extract_patent_id(url),
            "Title": f"Error: {str(e)}",
            "Abstract": f"Error: {str(e)}"
        }


def main():
    parser = argparse.ArgumentParser(description='Extract title and abstract from Google Patents URLs')
    parser.add_argument('-i', '--input', help='Patent URL to scrape')
    
    args = parser.parse_args()
    
    urls = []
    
    if args.input:
        urls.append(args.input)
    
    if not sys.stdin.isatty():
        for line in sys.stdin:
            url = line.strip()
            if url:
                urls.append(url)
    
    if not urls:
        parser.print_help()
        sys.exit(1)
    
    results = []
    for url in urls:
        if not url.startswith('http'):
            print(f"Error: Invalid URL format: {url}", file=sys.stderr)
            continue
            
        result = scrape_patent_info(url)
        results.append(result)
    
    if len(results) == 1:
        print(json.dumps(results[0], ensure_ascii=False, indent=2))
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
