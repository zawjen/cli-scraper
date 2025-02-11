import json
import os
from bs4 import BeautifulSoup



class Converter:
    def __init__(self, save_dir):
        self.save_dir = save_dir
        self.json_dir = os.path.join(save_dir, 'json')
        os.makedirs(self.json_dir, exist_ok=True)

    def convert_html_to_json(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
        data = {
            'title': soup.title.string if soup.title else '',
            'text': soup.get_text(separator='\n', strip=True)
        }
        json_file = os.path.join(self.json_dir, os.path.basename(file_path).replace('.html', '.json'))
        with open(json_file, 'w', encoding='utf-8') as json_f:
            json.dump(data, json_f, indent=4, ensure_ascii=False)

    def start_conversion(self):
        for file in os.listdir(self.save_dir):
            if file.endswith('.html'):
                self.convert_html_to_json(os.path.join(self.save_dir, file))

