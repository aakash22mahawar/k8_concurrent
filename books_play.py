from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time


def main():
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto('https://books.toscrape.com/')
        page.wait_for_timeout(5000)
        src = page.content()
        soup = BeautifulSoup(src, 'lxml')
        links = ['https://books.toscrape.com/' + x['href'] for x in soup.select('h3 > a')]

        for link in links:
            #print(link)
            page.goto(link)
            page.wait_for_timeout(2000)
            src = page.content()
            soup = BeautifulSoup(src, 'lxml')

            # Get the text from the first matching element
            name = soup.select_one('div.col-sm-6.product_main > h1').text
            price = soup.select_one('div.col-sm-6.product_main > p.price_color').text
            upc = soup.select_one('table.table.table-striped > tbody > tr > td').text

            item = {'name': name, 'price': price, 'upc': upc}
            print(item)

        browser.close()


if __name__ == '__main__':
    start = time.time()
    main()
    end = time.time()
    print(round((end - start), 4), '****Time in Seconds****')
