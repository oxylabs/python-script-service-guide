# Python Script As A Service


[<img src="https://img.shields.io/static/v1?label=&message=python&color=brightgreen" />](https://github.com/topics/python)
[<img src="https://img.shields.io/static/v1?label=&message=service&color=yellow" />](https://github.com/topics/service)
[<img src="https://img.shields.io/static/v1?label=&message=Web%20Scraping&color=important" />](https://github.com/topics/web-scraping)

- [Setting Up](#setting-up)
- [Create A Systemd Service](#create-a-systemd-service)
- [Create A Windows Service](#create-a-windows-service)
- [Easier Windows Service Using NSSM](#easier-windows-service-using-nssm)

A service (also known as a "daemon") is a process that performs tasks in the background and responds to system events.

Services can be written using any language. We use Python in these examples as it is one of the most versatile languages out there.

For more information, be sure to read [our blogpost on the subject](https://oxylabs.io/blog/python-script-service-guide).

## Setting Up

To run any of the examples, you will need Python 3. We also recommend [using a virtual environment](https://docs.python.org/3/library/venv.html).

```bash
python3 -m venv venv
```

## Create A Systemd Service

First, create a script that scrapes a website. Make sure the script also handles OS signals so that it exits gracefully.

**linux_scrape.py:**
```python
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
```

Then, create a systemd configuration file.

**/etc/systemd/system/book-scraper.service:**
```
[Unit]
Description=A script for scraping the book information
After=syslog.target network.target

[Service]
WorkingDirectory=/home/oxylabs/python-script-service/src/systemd
ExecStart=/home/oxylabs/python-script-service/venv/bin/python3 main.py

Restart=always
RestartSec=120

[Install]
WantedBy=multi-user.target
```
Make sure to adjust the paths based on your actual script location.

A fully working example can be found [here](src/systemd/linux_scrape.py).

## Create A Windows Service

To create a Windows service, you will need to implement methods such as `SvcDoRun` and `SvcStop` and handle events sent by the operating system.

**windows_scrape.py:**
```python
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
```

Next, install dependencies and run a post-install script. 

```
PS C:\> cd C:\Users\User\Scraper
PS C:\Users\User\Scraper> .\venv\Scripts\pip install pypiwin32
PS C:\Users\User\Scraper> .\venv\Scripts\pywin32_postinstall.py -install
```

Bundle your script into an executable.
```
PS C:\Users\User\Scraper> venv\Scripts\pyinstaller --hiddenimport win32timezone -F scrape.py
```

And finally, install your newly-created service.
```
PS C:\Users\User\Scraper> .\dist\scrape.exe install
Installing service BookScraper
Changing service configuration
Service updated

PS C:\Users\User\Scraper> .\dist\scrape.exe start
Starting service BookScraper
PS C:\Users\User\Scripts>
```

A fully working example can be found [here](src/windows-service/windows_scrape.py).

## Easier Windows Service Using NSSM

Instead of dealing with the Windows service layer directly, you can use the NSSM (Non-Sucking Service Manager).

Install NSSM by visiting [the official website](https://nssm.cc/download). Extract it to a folder of your choice and add the folder to your PATH environment variable for convenience.

Once you have NSSM installed, simplify your script by getting rid of all Windows-specific methods and definitions.

**simple_scrape.py:**
```python
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
```

Bundle your script into an executable.
```
PS C:\Users\User\Scraper> venv\Scripts\pyinstaller -F simple_scrape.py
```

And finally, install the script using NSSM.
```
PS C:\> nssm.exe install SimpleScrape C:\Users\User\Scraper\dist\simple_scrape.exe
PS C:\Users\User\Scraper> .\venv\Scripts\pip install pypiwin32
```

A fully working script can be found [here](src/nssm/simple_scrape.py).