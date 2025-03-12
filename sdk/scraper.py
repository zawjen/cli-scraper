import os
import random
import time
import requests
import threading
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from fake_useragent import UserAgent
from pathlib import Path

class Scraper:

    

    def __init__(self, base_url, save_dir):
        self.base_url = base_url.rstrip('/')
        self.save_dir = save_dir
        self.visited = set()
        self.parsed = set()
        self.lock = threading.Lock()
        os.makedirs(save_dir, exist_ok=True)

    # Function to get a random user-agent
    def get_user_agent(self):
        ua = UserAgent()
        return ua.random
    
    # Function to rotate through proxies (this is just an example, you should replace it with your proxy list)
    def get_proxy(self):
        proxies = [
            "http://123.123.123.123:8080",
            "http://124.124.124.124:3128",
            "http://125.125.125.125:9000",
        ]
        return {"http": random.choice(proxies), "https": random.choice(proxies)}

    def save_page(self, url, content):
        parsed_url = urlparse(url)
        path = parsed_url.path.strip('/') or 'index.html'
        file_path = os.path.join(self.save_dir, path.replace('/', '_') + '.html')
        
        #added by Kashif
        self.parsed.add(path)
        
        #if not path.endswith('/1'):
        with open('parsed_url.txt', '+a') as f:
            f.write(f'{path}\n')

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return file_path
        

    def scrape_page(self, url):
        if url in self.visited:
            return
        
        parsed_url = urlparse(url)
        path = parsed_url.path.strip('/') or 'index.html'

        if path in self.parsed and not path.startswith('tafseer'):
            return
        
        with self.lock:
            self.visited.add(url)
        try:
            headers = {
                    "User-Agent": self.get_user_agent()
                }
            
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                if path not in self.parsed:
                    file_path = self.save_page(url, response.text)
                soup = BeautifulSoup(response.text, 'html.parser')
                for link in soup.find_all('a', href=True):
                    next_url = urljoin(url, link['href'])
                    if next_url.startswith(self.base_url):                        
                        self.scrape_page(next_url)
        except requests.RequestException as e:
            print(f"Error scraping {url}: {e}")
    
    def scrape_tafseer(self, url):
        if url in self.visited:
            return
        
        parsed_url = urlparse(url)
        path = parsed_url.path.strip('/') or 'index.html'

        if path in self.parsed and not path.startswith('tafseer'):
            return
        
        
        with self.lock:
            self.visited.add(url)
        try:
            orig_url = url
            if "%j" in orig_url:
                for j in range(1,999):
                    url = orig_url.replace('%j', str(j))
                    
                    file_path = os.path.join(self.save_dir, path.replace('/', '_').replace('%j', str(j)) + '.html')
                
                    file = Path(file_path)
                    # Check if file exists
                    if file.exists():
                        continue
            
                    headers = {
                        "User-Agent": self.get_user_agent()
                    }
                
                    response = requests.get(url, headers=headers, timeout=10)
                    # response = requests.get(url)
                    if response.status_code == 200:
                        file_path = self.save_page(url, response.text)
                    else:
                        if response.status_code == 500:
                            return
                    time.sleep(random.randint(1,3)) 
            else:
                url = orig_url
                response = requests.get(url)
                if response.status_code == 200:
                    file_path = self.save_page(url, response.text)
                else:
                    if response.status_code == 500:
                        return
                time.sleep(random.randint(1,3))
            

        except requests.RequestException as e:
            print(f"Error scraping {url}: {e}")

    def start_scraping(self):
        try:
            with open('parsed_url.txt', 'r') as f:
                contents = f.read()
                for url in contents.split('\n'):
                    if url != '':
                        self.parsed.add(url)


        except:
            print()

        self.scrape_page(self.base_url)
    
    def start_urllist_scraping(self):
        try:
            with open('parsed_url.txt', 'r') as f:
                contents = f.read()
                for url in contents.split('\n'):
                    if url != '':
                        self.parsed.add(url)


        except:
            print()

        with open('to_be_parsed.txt', 'r') as f:
            contents = f.readline().strip()
            while contents != "" :
                if '%i' in contents:
                    for x in range(1,115):
                        try:
                            self.scrape_tafseer(urljoin(self.base_url, contents.replace('%i', str(x))))
                        except:
                            {}
                else:
                    self.scrape_tafseer(urljoin(self.base_url, contents))
                contents = f.readline().strip()
