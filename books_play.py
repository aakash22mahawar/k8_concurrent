import time
import asyncio
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
from connection import create_connection, close_connection

async def scrape_book_details(page, link):
    """Scrape the details of a book given its link."""
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

        return {'name': name, 'price': price, 'upc': upc}
    except Exception as e:
        print(f"Error scraping {link}: {e}")
        return None

def insert_into_db(book_details):
    """Insert scraped book details into MySQL database."""
    connection = create_connection()
    if connection:
        try:
            cursor = connection.cursor()
            insert_query = """
                INSERT INTO books (name, price, upc) 
                VALUES (%s, %s, %s)
            """
            for book in book_details:
                cursor.execute(insert_query, (book['name'], book['price'], book['upc']))
                print("Data inserted successfully into table books")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            close_connection(connection)

async def run(playwright):
    browser = await playwright.firefox.launch(headless=True)
    try:
        page = await browser.new_page()
        # Disabling images and other media
        await page.route("**/*", lambda route: asyncio.create_task(route.abort()) if route.request.resource_type in ["image", "stylesheet", "font"] else asyncio.create_task(route.continue_()))
        # Navigate to the main page
        url = 'https://books.toscrape.com/'
        await page.goto(url)
        print("Navigating to URL:", url)
        await page.wait_for_load_state('networkidle')
        print("URL loaded successfully")

        # Get the links to all books
        content = await page.content()
        soup = BeautifulSoup(content, 'lxml')
        links = ['https://books.toscrape.com/' + a['href'] for a in soup.select('h3 > a')]

        # Scrape each book's details concurrently using the same page
        book_details = []
        for link in links:
            details = await scrape_book_details(page, link)
            if details:
                book_details.append(details)

        # Print or return the collected details
        for book in book_details:
            print(book)

        # Insert the scraped data into the database
        insert_into_db(book_details)

    finally:
        await browser.close()

async def main():
    async with async_playwright() as playwright:
        await run(playwright)

if __name__ == '__main__':
    start = time.time()
    asyncio.run(main())
    end = time.time()
    print(round((end - start), 4), '****Time in Seconds****')
