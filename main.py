
import os
import threading
from urllib.parse import urlparse
from sdk.command_line_handler import CommandLineHandler
from sdk.converter import Converter
from sdk.scraper import Scraper


def main():
    cli_handler = CommandLineHandler()
    args = cli_handler.parse_args()
    base_url = args.url
    downloads_dir = r"./downloads"
    save_dir = os.path.join(downloads_dir, urlparse(base_url).netloc)
    
    scraper = Scraper(base_url, save_dir)
    scraper_thread = threading.Thread(target=scraper.start_scraping)
    scraper_thread.start()
    scraper_thread.join()  # Ensure scraping completes before JSON conversion starts

    converter = Converter(save_dir)
    converter_thread = threading.Thread(target=converter.start_conversion)
    converter_thread.start()
    converter_thread.join()

if __name__ == "__main__":
    main()