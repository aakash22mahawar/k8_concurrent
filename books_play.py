import time
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from connection import create_connection, close_connection


async def scrape_book_details(page, link, cursor, connection):
    """Scrape the details of a book given its link and insert into DB."""
    try:
        await page.goto(link)
        await page.wait_for_load_state('networkidle')

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
        cursor.execute(insert_query, (item['name'], item['price'], item['upc']))
        print("++++ item inserted successfully ++++")

    except Exception as e:
        print(f"Error scraping {link}: {e}")


async def scrape_books_from_pages(page, start_page, end_page, cursor, connection):
    """Scrape books from a range of pages."""
    for page_num in range(start_page, end_page + 1):
        page_url = f'https://books.toscrape.com/catalogue/page-{page_num}.html'
        print(f"Navigating to URL: {page_url}")
        await page.goto(page_url)
        await page.wait_for_load_state('networkidle')
        print(f"URL {page_url} loaded successfully")

        # Get the links to all books on the current page
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        links = ['https://books.toscrape.com/catalogue/' + a['href'] for a in soup.select('h3 > a')]

        # Scrape and insert each book's details into the database
        for link in links:
            await scrape_book_details(page, link, cursor, connection)

        # Introduce a delay of 2 seconds before proceeding to the next page
        await asyncio.sleep(2)


async def run(playwright):
    browser = await playwright.firefox.launch(headless=True)
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            page = await browser.new_page()
            # Disabling images and other media
            await page.route("**/*",
                             lambda route: asyncio.create_task(route.abort()) if route.request.resource_type in [
                                 "image", "stylesheet", "font"] else asyncio.create_task(route.continue_()))

            # Scrape books from page 1 to page 10
            await scrape_books_from_pages(page, 1, 10, cursor, connection)

        finally:
            close_connection(connection)
            await browser.close()


async def main():
    async with async_playwright() as playwright:
        await run(playwright)


if __name__ == '__main__':
    start = time.time()
    asyncio.run(main())
    end = time.time()
    print(round((end - start), 4), '****Time in Seconds****')
