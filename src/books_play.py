import time
import asyncio
from book_scraper import BookScraper
from playwright.async_api import async_playwright
from connection import create_connection, close_connection

class BookPlay:
    def __init__(self, num_browsers, total_pages, max_concurrent_browsers):
        self.num_browsers = num_browsers
        self.total_pages = total_pages
        self.max_concurrent_browsers = max_concurrent_browsers
        self.semaphore = asyncio.Semaphore(max_concurrent_browsers)

    async def scrape_with_browser(self, playwright, start_page, end_page):
        async with self.semaphore:  # Ensure only `max_concurrent_browsers` browsers run concurrently
            browser = None
            try:
                browser = await playwright.firefox.launch(
                    headless=True,
                    args=["--no-sandbox", "--disable-gpu"]
                )
                connection = create_connection()
                if connection:
                    try:
                        cursor = connection.cursor()
                        page = await browser.new_page()

                        # Disabling images and other media
                        await page.route("**/*", lambda route: asyncio.create_task(
                            route.abort()) if route.request.resource_type in ["image", "stylesheet", "font"]
                                        else asyncio.create_task(route.continue_()))

                        # Instantiate the Scraper class and start scraping
                        scraper = BookScraper(cursor, connection)
                        await scraper.scrape_books_from_pages(page, start_page, end_page)

                    except Exception as e:
                        print(f"Error during scraping: {e}")
                    finally:
                        close_connection(connection)
                        await page.close()
            except Exception as e:
                print(f"Error launching or managing browser: {e}")
            finally:
                if browser:
                    await browser.close()

    async def run(self, playwright):
        pages_per_browser = self.total_pages // self.num_browsers
        tasks = []

        for i in range(self.num_browsers):
            start_page = i * pages_per_browser + 1
            end_page = (i + 1) * pages_per_browser if i < self.num_browsers - 1 else self.total_pages
            tasks.append(self.scrape_with_browser(playwright, start_page, end_page))

        await asyncio.gather(*tasks)

    async def main(self):
        async with async_playwright() as playwright:
            await self.run(playwright)

if __name__ == '__main__':
    start = time.time()
    scraper = BookPlay(num_browsers=10, total_pages=20, max_concurrent_browsers=8)
    asyncio.run(scraper.main())
    end = time.time()
    print(round((end - start), 4), '****Time in Seconds****')
