import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

urls = ['https://books.toscrape.com/catalogue/sapiens-a-brief-history-of-humankind_996/index.html',
        'https://books.toscrape.com/catalogue/shakespeares-sonnets_989/index.html',
        'https://books.toscrape.com/catalogue/sharp-objects_997/index.html', ]

index = 0

while True:
    url = urls[index % len(urls)]
    index += 1

    print('Scraping url', url)
    response = requests.get(url)

    soup = BeautifulSoup(response.content, 'html.parser')
    book_name = soup.select_one('.product_main').h1.text
    rows = soup.select('.table.table-striped tr')
    product_info = {row.th.text: row.td.text for row in rows}

    data_folder = Path('C:\\Users\\User\\Scraper\\data')
    data_folder.mkdir(parents=True, exist_ok=True)

    json_file_name = re.sub('[\': ]', '-', book_name)
    json_file_path = data_folder / f'{json_file_name}.json'
    with open(json_file_path, 'w') as book_file:
        json.dump(product_info, book_file)
