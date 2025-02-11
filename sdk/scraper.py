import os
import requests
import threading
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class Scraper:
    def __init__(self, base_url, save_dir):
        self.base_url = base_url.rstrip('/')
        self.save_dir = save_dir
        self.visited = set()
        self.lock = threading.Lock()
        os.makedirs(save_dir, exist_ok=True)

    def save_page(self, url, content):
        parsed_url = urlparse(url)
        path = parsed_url.path.strip('/') or 'index.html'
        file_path = os.path.join(self.save_dir, path.replace('/', '_') + '.html')
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return file_path

    def scrape_page(self, url):
        if url in self.visited:
            return
        with self.lock:
            self.visited.add(url)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                file_path = self.save_page(url, response.text)
                soup = BeautifulSoup(response.text, 'html.parser')
                for link in soup.find_all('a', href=True):
                    next_url = urljoin(url, link['href'])
                    if next_url.startswith(self.base_url):
                        self.scrape_page(next_url)
        except requests.RequestException as e:
            print(f"Error scraping {url}: {e}")

    def start_scraping(self):
        self.scrape_page(self.base_url)
