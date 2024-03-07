import requests
import random
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime


# List of user agents to rotate
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Safari/605.1.15",
    # Add more user agents as needed
]

def fetch_json_urls(page_url):
    response = requests.get(page_url, timeout=30)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        participating_retailers_section = soup.find('h2', id='participating-retailers')
        table = participating_retailers_section.find_next('table')
        retailer_data = []
        for row in table.find_all('tr')[1:]:
            cells = row.find_all('td')
            if len(cells) > 1:
                retailer_name = cells[0].text.strip()
                if cells[1].contents:
                    first_element = cells[1].contents[0]
                    if hasattr(first_element, 'text'):
                        str_out = first_element.text.strip()
                    else:
                        str_out = str(first_element).strip()
                else:
                    str_out = ''
                link_tag = str_out
                if link_tag:
                    retailer_data.append((retailer_name, link_tag))
        return retailer_data
    else:
        print("Failed to fetch the webpage")
        return []

session = requests.Session()
session.headers.update({'User-Agent': random.choice(USER_AGENTS)})

def attempt_download(download_url):
    try:
        
        user_agent = random.choice(USER_AGENTS)
        headers = {'User-Agent': user_agent,
                    'Accept': 'application/json',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive'
                  }
        session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
        
        response = session.get(download_url, headers=headers, timeout=10)
        response.raise_for_status()  # Raises stored HTTPError, if one occurred.
        return response.json()
    except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
        print(f"Failed to download {download_url}: {e}")
        return e

def download_json_files(retailer_data, base_directory):
    today = datetime.now().strftime("%Y-%m-%d")

    for retailer_name, url in retailer_data:
        retailer_dir = os.path.join(base_directory, retailer_name.replace("/", "-"))
        os.makedirs(retailer_dir, exist_ok=True)

        filename = f"{retailer_name.replace('/', '-')}_{today}.json"
        file_path = os.path.join(retailer_dir, filename)

        data = attempt_download(url)

        if not isinstance(data, Exception):
            with open(file_path, 'w') as file:
                json.dump(data, file)
            print(f"Downloaded: {file_path}")
        else:
            print(f"Failed to download and process: {url}")

# URL of the page to scrape and base directory setup
page_url = "https://www.gov.uk/guidance/access-fuel-price-data"
base_directory = './json_files_by_retailer/'

# Fetch JSON URLs and retailer names
retailer_data = fetch_json_urls(page_url)

# Download JSON files, including retailer names, to retailer-specific directories
download_json_files(retailer_data, base_directory)
