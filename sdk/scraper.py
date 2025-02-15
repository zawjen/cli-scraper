import os
import json
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class Scraper:
    def __init__(self, base_url, save_dir="quran_data"):
        self.base_url = base_url
        self.save_dir = save_dir
        self.visited = set()
        self.driver = self.init_selenium()
        self.base_domain = urlparse(base_url).netloc
        self.wait = WebDriverWait(self.driver, 30)

        os.makedirs(save_dir, exist_ok=True)

    def init_selenium(self):
        """Initialize and configure Chrome WebDriver"""
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])

        driver = webdriver.Chrome(options=chrome_options)
        driver.set_page_load_timeout(40)
        driver.execute_cdp_cmd(
            "Network.setUserAgentOverride",
            {
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
        )
        return driver

    def start_scraping(self):
        """Main controller for scraping process"""
        try:
            print("🚀 Starting Quran website scraper...")
            self.process_page(self.base_url)
            print("\n✅ Scraping completed successfully!")
        except Exception as e:
            print(f"\n❌ Scraping interrupted by error: {str(e)}")
        finally:
            self.driver.quit()
            print(f"📊 Total pages scraped: {len(self.visited)}")

    def process_page(self, url):
        """Process individual page with full content extraction"""
        if url in self.visited:
            return
        self.visited.add(url)

        print(f"\n📄 Processing: {url}")

        try:
            # Load page with Selenium
            self.driver.get(url)
            self.wait.until(EC.presence_of_element_located((By.XPATH, "//*[not(self::script or self::style)]")))

            # Handle JavaScript-rendered content
            self.handle_dynamic_content()

            # Parse and extract content
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            page_data = self.extract_all_content(soup, url)
            self.save_as_json(page_data)

            # Process discovered links
            for link in page_data["links"]:
                if self.should_crawl(link):
                    self.process_page(link)

        except Exception as e:
            print(f"⚠️ Error processing {url}: {str(e)}")

    def handle_dynamic_content(self):
        """Handle JavaScript-rendered content"""
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        time.sleep(2)
        self.driver.execute_script("window.scrollTo(0, 0);")

    def extract_all_content(self, soup, url):
        """Extract all content from the page"""
        return {
            "url": url,
            "title": self.get_title(soup),
            "metadata": self.get_metadata(soup),
            "content": self.get_structured_content(soup),
            "verses": self.extract_verses(soup),
            "images": self.extract_images(soup, url),
            "links": self.extract_links(soup, url),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
        }

    def get_title(self, soup):
        """Extract page title"""
        title = soup.find('title')
        return title.get_text(strip=True) if title else ""

    def get_metadata(self, soup):
        """Extract metadata (SEO, OpenGraph, etc.)"""
        meta_data = {}
        for tag in soup.find_all('meta'):
            name = tag.get('name') or tag.get('property') or tag.get('itemprop')
            content = tag.get('content')
            if name and content:
                meta_data[name.lower()] = content
        return meta_data

    def get_structured_content(self, soup):
        """Extract all structured content recursively"""
        return self.process_child_elements(soup.body)  # Start from <body>

    def process_child_elements(self, parent_element):
        """Process all elements recursively"""
        children = []
        for child in parent_element.find_all(recursive=False):
            child_data = {
                "type": child.name,
                "text": self.clean_text(child.get_text()),
                "attributes": self.get_element_attributes(child)
            }
            if child.find_all(recursive=False):
                child_data["children"] = self.process_child_elements(child)
            children.append(child_data)
        return children

    def extract_verses(self, soup):
        """Extract all text content (including Quranic verses)"""
        verses = []
        for verse in soup.find_all(lambda tag: tag.name not in ['script', 'style'] and tag.get_text(strip=True)):
            verses.append({
                "text": self.clean_text(verse.get_text()),
                "attributes": self.get_element_attributes(verse)
            })
        return verses

    def extract_images(self, soup, base_url):
        """Extract all images"""
        images = []
        for img in soup.find_all('img'):
            try:
                src = img.get('src') or img.get('data-src')
                if not src:
                    continue
                images.append({
                    "url": urljoin(base_url, src),
                    "alt": img.get('alt', ''),
                    "width": img.get('width'),
                    "height": img.get('height'),
                })
            except Exception as e:
                print(f"⚠️ Error processing image: {str(e)}")
        return images

    def extract_links(self, soup, base_url):
        """Extract all internal links"""
        links = set()
        for a in soup.find_all('a', href=True):
            try:
                href = a['href']
                full_url = urljoin(base_url, href)
                normalized = self.normalize_url(full_url)
                if self.is_valid_link(normalized):
                    links.add(normalized)
            except Exception as e:
                print(f"⚠️ Error processing link: {str(e)}")
        return list(links)

    def normalize_url(self, url):
        """Normalize URL format"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path.rstrip('/')}"

    def is_valid_link(self, url):
        """Validate if URL should be crawled"""
        parsed = urlparse(url)
        return (
            parsed.scheme in ['http', 'https'] and
            parsed.netloc == self.base_domain
        )

    def save_as_json(self, data):
        """Save extracted data to JSON"""
        parsed = urlparse(data['url'])
        file_path = os.path.join(self.save_dir, f"{parsed.path.strip('/').replace('/', '_') or 'index'}.json")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved: {file_path}")

    def should_crawl(self, url):
        """Check if URL should be processed"""
        return url not in self.visited and self.is_valid_link(url)

    @staticmethod
    def clean_text(text):
        """Clean text content"""
        return ' '.join(text.strip().split())

    @staticmethod
    def get_element_attributes(element):
        """Extract attributes of an element"""
        return {'id': element.get('id'), 'classes': element.get('class', [])}