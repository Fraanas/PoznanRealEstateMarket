import logging
import os
import sys
import time
from datetime import datetime
from urllib.parse import urljoin
import random

import pandas as pd
import requests
from bs4 import BeautifulSoup

sys.path.append("config")
sys.path.append("data")

from config.elements import SCRAPING_CONFIG
from config.scraper_config import BASE_URL, MAIN_URL, HEADERS
from src.transforming.transform import transform_data
from src.database.data_loader import insert_data

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



class WebScraper:
    def __init__(self, main_url=MAIN_URL, base_url=BASE_URL, headers=HEADERS, max_pages=1, output_dir="../project/data" ):
        self.main_url = main_url
        self.base_url = base_url
        self.headers = headers
        self.max_pages = max_pages
        self.output_dir = output_dir

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    @staticmethod
    def safe_extract(soup, tag, attrs, index=None, remove_text=None):
        """
        Extracts text from an element
        Args:
            soup (BeautifulSoup): BeautifulSoup object to search
            tag (str): Tag to find
            attrs (dict): Attributes to match
            index (int, optional): Index of the element if list
            remove_text (str or list, optional): Text to remove
        Returns:
            str or None: Extracted text or None
        """
        try:
            # find elements
            elements = soup.find_all(tag, attrs=attrs)
            element = elements[index] if index is not None else elements[0] if elements else None
            if element:
                text = element.text.strip()
                if remove_text:
                    if isinstance(remove_text, list):
                        for txt in remove_text:
                            text = text.replace(txt, '')
                    else:
                        text = text.replace(remove_text, '')
                return text.replace(' ', '')
            return None

        except (IndexError, AttributeError):
            return None

    @staticmethod
    def safe_extract_info(soup, tag, attrs):
        """
        Extracts key-value pairs from property info section.
        Args:
            soup (BeautifulSoup): BeautifulSoup object to search
            tag (str): Tag to find
            attrs (dict): Attributes to match
        Returns:
            dict: Dictionary with extracted key-value pairs
        """
        try:
            elements = soup.find_all(tag, attrs=attrs)
            if not elements:
                logger.warning("No elements found in info section")
                return {}

            text_list = [el.get_text(strip=True) for el in elements]
            if not text_list:
                logger.warning("Extracted info is empty")
                return {}

            # create key:value
            data = {}
            for i in range(0, len(text_list) - 1, 2):
                key = text_list[i].replace(":", "").strip()
                value = text_list[i + 1].strip()
                if value.lower() == "brak informacji":
                    value = None
                data[key] = value

            logger.info(f"Extracted info data: {data}")
            return data
        except Exception as e:
            logger.error(f"Error extracting info section: {e}")
            return {}



    def get_links(self):
        """
        Takes links to properties from multiple sites
        Args:
            main_url (str): The main URL to scrape
            base_url (str): Base URL of the page
            max_pages (int): Maximum number of pages to scrape
        Returns:
            list: List of links to the property
        """
        all_links = []

        for page in range(1, self.max_pages + 1):
            # Add page numer to URL
            page_url = f"{self.main_url}&page={page}"

            try:
                response = requests.get(page_url, headers=HEADERS)
                response.raise_for_status()
                soup = BeautifulSoup(response.text, "html.parser")
                # Fetch links on current page
                links = soup.find_all('a', attrs={'data-cy': 'listing-item-link'})
                page_links = [urljoin(self.base_url, link['href']) for link in links if link.get('href')]
                # add links to list
                all_links.extend(page_links)
                # stop if there are no more pages
                if not page_links:
                    break
                time.sleep(random.uniform(0.5,2.5))  # Delay beetween requests

            except Exception as e:
                logger.error(f"Error while downloading the page {page}: {e}")
                break

        print(f"We have {len(all_links)} links")
        return all_links




    def scrape_listing(self, url):
        """
        Retrieves details of a single property
        Args:
            url (str): URL of the property
        Returns:
            dict: property details
        """
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            current_date = datetime.now().strftime("%Y-%m-%d")

            listing_data = {
                'property_id': WebScraper.safe_extract(soup, **SCRAPING_CONFIG['property_id']),
                'price': WebScraper.safe_extract(soup, **SCRAPING_CONFIG['price']),
                'square': WebScraper.safe_extract(soup, **SCRAPING_CONFIG['square']),
                'price_per_sqm': WebScraper.safe_extract(soup, **SCRAPING_CONFIG['price_per_sqm']),
                'rooms': WebScraper.safe_extract(soup, **SCRAPING_CONFIG['rooms']),
                'location': WebScraper.safe_extract(soup, **SCRAPING_CONFIG['location']),
                'info' : WebScraper.safe_extract_info(soup, **SCRAPING_CONFIG['info']),
                'date': current_date,
                'url': url
            }
            return transform_data(listing_data)

        except Exception as e:
            logger.error(f"Error during the scraping {url}: {e}")
            return None



    def scrape_all_listings(self, links_list):
        """
        Retrieves data from all links
        Args:
            links_list (list): List of links to properties
        Returns:
            pandas.DataFrame: DataFrame with property data
        """
        all_data = []

        for url in links_list:
            logger.info(f"Scraping: {url}")
            listing_data = self.scrape_listing(url)
            if listing_data:
                all_data.append(listing_data)
            time.sleep(random.uniform(0.5,2.5))

        return pd.DataFrame(all_data)




    def save_to_file(self, df, filename="poznan_properties.csv"):
        '''
        Save data to csv file
        '''
        file_path = os.path.join(self.output_dir, filename)
        df.to_csv(file_path, index=False)
        logger.info(f"Saving data to {file_path}")


    def save_to_db(self, df):
        '''
        Save data to csv file
        '''
        try:
            #df = df.fillna('')
            data = df[['property_id', 'price', 'square', 'price_per_sqm', 'rooms', 'date', 'url',
                        'street', 'district_1', 'district_2', 'city', 'state', 'heating', 'floor',
                        'rent', 'bld_condition', 'market', 'ownership', 'availability', 'seller_type',
                        'extra_info', 'elevator', 'building_type', 'building_year', 'security',
                        'media', 'building_material', 'windows', 'equipment']].values.tolist()

            logger.info(f"Columns in DataFrame before saving: {df.columns.tolist()}")
            logger.info(f"First row: {df.iloc[0].to_dict()}")

            insert_data(data)
            logger.info(f"Successfully saved {len(data)} properties to the database.")

        except Exception as e:
            logger.error(f"Error saving data to database: {e}")



    def run(self):
        links_list = self.get_links()
        df_listing = self.scrape_all_listings(links_list)
        #self.save_to_file(df_listing)
        self.save_to_db(df_listing)
        print(f"Successfully scraped {len(df_listing)} properties")