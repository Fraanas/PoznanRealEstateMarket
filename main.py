from src.scraping.scraper import WebScraper

if __name__ == "__main__":
    scraper = WebScraper(max_pages=1)
    scraper.run()
