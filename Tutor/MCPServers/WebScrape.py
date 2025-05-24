'''
This script will be used to create a MCP server that provides our WebScrape service.
'''

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from mcp.server.fastmcp import FastMCP
from Tutor.Tools.WebScrape import WebScrape
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

class WebScrapeServer:
    def __init__(self):
        try:
            logger.info("[WebScrape MCP Server] Initializing WebScrape MCP Server...")
            logger.info("[WebScrape MCP Server] Creating WebScrape instance...")
            self.web_scrape = WebScrape()
            logger.info("[WebScrape MCP Server] WebScrape instance created successfully.")
            logger.info("[WebScrape MCP Server] Creating FastMCP instance...")
            self.mcp = FastMCP("web-scrape")
            logger.info("[WebScrape MCP Server] FastMCP instance created successfully.")
            logger.info("[WebScrape MCP Server] WebScrape MCP Server initialized successfully.")
        except TutorException as e:
            logger.error("[WebScrape MCP Server] Failed to initialize WebScrape MCP Server")
            raise TutorException(e, sys)
        
        scraping_tool = self.web_scrape
        @self.mcp.tool()
        async def scrape_info(url: str):
            """
            Scrape the content of the given URL.
            Args:
                url (str): The URL to scrape.
            Returns:
                Langchain Document
            """
            try:
                logger.info("[WebScrape MCP Server] Providing WebScrape service...")
                result = scraping_tool.scrape(url=url)
                logger.info("[WebScrape MCP Server] WebScrape service provided successfully.")
                return result
            except TutorException as e:
                logger.error("[WebScrape MCP Server] Error occurred while providing WebScrape service")
                raise TutorException(e, sys)
            
    def serve(self):
        try:
            logger.info("[WebScrape MCP Server] Starting WebScrape MCP Server...")
            self.mcp.run(transport='stdio')
        except TutorException as e:
            logger.error(f"[WebScrape MCP Server] Failed to start WebScrape MCP Server")
            raise TutorException(e, sys)

def main():
    logger.info("[WebScrape MCP Server] main() function of web scrape server called")
    server = WebScrapeServer()
    logger.info("[WebScrape MCP Server] WebScrapeServer instance created")
    server.serve()

if __name__ == "__main__":
    main()