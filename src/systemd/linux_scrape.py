import json
import re
import signal
from pathlib import Path
import requests
from bs4 import BeautifulSoup


class SignalHandler:
    shutdown_requested = False

    def __init__(self):
        signal.signal(signal.SIGINT, self.request_shutdown)
        signal.signal(signal.SIGTERM, self.request_shutdown)

    def request_shutdown(self, *args):
        print('Request to shutdown received, stopping')
        self.shutdown_requested = True

    def can_run(self):
        return not self.shutdown_requested


signal_handler = SignalHandler()
urls = [
    'https://books.toscrape.com/catalogue/sapiens-a-brief-history-of-humankind_996/index.html',
    'https://books.toscrape.com/catalogue/shakespeares-sonnets_989/index.html',
    'https://books.toscrape.com/catalogue/sharp-objects_997/index.html',
]

index = 0
while signal_handler.can_run():
    url = urls[index % len(urls)]
    index += 1

    print('Scraping url', url)
    response = requests.get(url)

    soup = BeautifulSoup(response.content, 'html.parser')
    book_name = soup.select_one('.product_main').h1.text
    rows = soup.select('.table.table-striped tr')
    product_info = {row.th.text: row.td.text for row in rows}

    data_folder = Path('./data')
    data_folder.mkdir(parents=True, exist_ok=True)

    json_file_name = re.sub('[\': ]', '-', book_name)
    json_file_path = data_folder / f'{json_file_name}.json'
    with open(json_file_path, 'w') as book_file:
        json.dump(product_info, book_file)
