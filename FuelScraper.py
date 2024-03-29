import requests
import random
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
import dropbox

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

def upload_to_dropbox(folder_path, filename, data):
    # Initialize your Dropbox client with the token
    # dbx = dropbox.Dropbox(dbx_token)
    dbx = dropbox.Dropbox(
        app_key=dbx_app_tk,
        app_secret= dbx_app_sec,
        oauth2_refresh_token = dbx_token
        )
    
    dropbox_path = f"{folder_path}/{filename}"
    try:
        dbx.files_upload(data.encode(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
        print(f"Uploaded: {dropbox_path}")
    except Exception as e:
        print(f"Failed to upload {dropbox_path}: {e}")

def download_json_files(retailer_data, main_folder_name):
    today = datetime.now().strftime("%Y-%m-%d")
    
    for retailer_name, url in retailer_data:
        filename = f"{retailer_name.replace('/', '-')}_{today}.json"
        folder_path = f"/{main_folder_name}/{retailer_name.replace('/', '-')}"  # Construct path with main folder and subfolder

        data = attempt_download(url)

        if not isinstance(data, Exception):
            data_str = json.dumps(data)
            upload_to_dropbox(folder_path, filename, data_str)
        else:
            print(f"Failed to download and process: {url}")

# URL of the page to scrape and base directory setup
page_url = "https://www.gov.uk/guidance/access-fuel-price-data"
base_directory = './json_files_by_retailer/'

# Access the DROPBOX_ACCESS_TOKEN environment variable
dbx_token = os.environ.get("DROPBOX_ACCESS_TOKEN")
dbx_app_sec = os.environ.get("DROPBOX_APP_SECRET")
dbx_app_tk = os.environ.get("DROPBOX_APP_KEY")

# Fetch JSON URLs and retailer names
retailer_data = fetch_json_urls(page_url)

# Main folder name in Dropbox
main_folder_name = "Fuel Data By Retailer"

# Assuming retailer_data is already defined and contains your data
download_json_files(retailer_data, main_folder_name)
