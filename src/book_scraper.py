import asyncio
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from connection import create_connection, close_connection

class BookScraper:
    def __init__(self, cursor, connection):
        self.cursor = cursor
        self.connection = connection

    async def scrape_book_details(self, page, link):
        """Scrape the details of a book given its link and insert into DB."""
        try:
            await page.goto(link)
            await page.wait_for_load_state('networkidle', timeout=60000)

            # Extract page content and parse with BeautifulSoup
            content = await page.content()
            soup = BeautifulSoup(content, 'lxml')

            # Extract details using BeautifulSoup
            name = soup.select_one('div.col-sm-6.product_main > h1').text
            price = soup.select_one('div.col-sm-6.product_main > p.price_color').text
            upc = soup.select_one('table.table.table-striped > tbody > tr > td').text
            item = {'name': name, 'price': price, 'upc': upc}
            print(item)

            # Insert the scraped data into the database immediately
            insert_query = """
                INSERT INTO books (name, price, upc) 
                VALUES (%s, %s, %s)
            """
            self.cursor.execute(insert_query, (item['name'], item['price'], item['upc']))
            print("++++ item inserted successfully ++++")

        except (PlaywrightTimeoutError, Exception) as e:
            print(f"Error scraping {link}: PlaywrightTimeoutError ")

    async def scrape_books_from_pages(self, page, start_page, end_page):
        """Scrape books from a range of pages."""
        for page_num in range(start_page, end_page + 1):
            page_url = f'https://books.toscrape.com/catalogue/page-{page_num}.html'
            print(f"Navigating to URL: {page_url}")
            try:
                await page.goto(page_url)
                await page.wait_for_load_state('networkidle',timeout=60000)
                print(f"URL {page_url} loaded successfully")

                # Get the links to all books on the current page
                content = await page.content()
                soup = BeautifulSoup(content, 'lxml')
                links = ['https://books.toscrape.com/catalogue/' + a['href'] for a in soup.select('h3 > a')]

                # Scrape and insert each book's details into the database
                for link in links:
                    await self.scrape_book_details(page, link)

                # Introduce a delay of 2 seconds before proceeding to the next page
                await asyncio.sleep(2)

            except (PlaywrightTimeoutError, Exception) as e:
                print(f"Error scraping {page_url}: PlaywrightTimeoutError")
