import sys
import servicemanager
import win32event
import win32service
import win32serviceutil
import json
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


class BookScraperService(win32serviceutil.ServiceFramework):
    _svc_name_ = 'BookScraperService'
    _svc_display_name_ = 'BookScraperService'
    _svc_description_ = 'Constantly updates the info about books'

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.event = win32event.CreateEvent(None, 0, 0, None)

    def GetAcceptedControls(self):
        result = win32serviceutil.ServiceFramework.GetAcceptedControls(self)
        result |= win32service.SERVICE_ACCEPT_PRESHUTDOWN
        return result

    def SvcDoRun(self):
        urls = [
            'https://books.toscrape.com/catalogue/sapiens-a-brief-history-of-humankind_996/index.html',
            'https://books.toscrape.com/catalogue/shakespeares-sonnets_989/index.html',
            'https://books.toscrape.com/catalogue/sharp-objects_997/index.html',
        ]

        index = 0

        while True:
            result = win32event.WaitForSingleObject(self.event, 5000)
            if result == win32event.WAIT_OBJECT_0:
                break

            url = urls[index % len(urls)]
            index += 1

            print('Scraping url', url)
            response = requests.get(url)

            soup = BeautifulSoup(response.content, 'html.parser')
            book_name = soup.select_one('.product_main').h1.text
            rows = soup.select('.table.table-striped tr')
            product_info = {row.th.text: row.td.text for row in rows}

            data_folder = Path('C:\\Users\\User\\Scraper\\dist\\scrape\\data')
            data_folder.mkdir(parents=True, exist_ok=True)

            json_file_name = re.sub('[\': ]', '-', book_name)
            json_file_path = data_folder / f'{json_file_name}.json'
            with open(json_file_path, 'w') as book_file:
                json.dump(product_info, book_file)

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.event)


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(BookScraperService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(BookScraperService)
