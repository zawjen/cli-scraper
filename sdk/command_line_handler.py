import argparse


class CommandLineHandler:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Web Scraper and Converter")
        self.parser.add_argument("url", type=str, help="Base URL to scrape")

    def parse_args(self):
        return self.parser.parse_args()