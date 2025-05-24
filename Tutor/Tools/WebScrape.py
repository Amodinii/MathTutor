'''
This file is essentially used to scrape the webpages, that were found by our WebSearch.py file.
'''

import sys
import os
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException
from langchain_community.document_loaders import ScrapingAntLoader
from dotenv import load_dotenv
load_dotenv()

class WebScrape:
    def __init__ (self):
        try:
            logger.info("Initializing WebScrape tool...")
            self.scrape_config = {
                "browser": True,
                "proxy_type": "datacenter",
                "proxy_country": "us"
            }
            logger.info("WebScrape tool initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing WebScrape tool")
            raise TutorException(e, sys)

    def scrape(self, url: str):
        try:
            print("Inside the tool")
            logger.info(f"Scraping URL: {url}")
            loader = ScrapingAntLoader(
                [url],
                api_key=os.getenv("SCRAPINGANT_TOKEN"),
                continue_on_failure=True,
                scrape_config=self.scrape_config
            )
            documents = loader.load()
            logger.info(f"Scraped {len(documents)} documents from {url}")
            return documents
        except Exception as e:
            logger.error(f"Error scraping URL")
            raise TutorException(e, sys)