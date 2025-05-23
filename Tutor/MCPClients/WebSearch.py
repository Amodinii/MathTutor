import sys
from mcp import Client
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

class WebSearchClient:
    def __init__(self, server_url: str = "http://localhost:6000"):
        try:
            logger.info(f"[WebSearch Client] Initializing WebSearch Client with server URL: {server_url}")
            self.client = Client(server_url)
            self.search_tool = self.client.tool("search")
        except Exception as e:
            logger.error("[WebSearch Client] Failed to initialize WebSearch Client.")
            raise TutorException(e, sys)

    def search(self, query: str):
        try:
            logger.info(f"[WebSearch Client] Performing web search for query: {query}")
            return self.search_tool.invoke({
                "query": query
            })
        except Exception as e:
            logger.error(f"[WebSearch Client] Error occurred while performing web search: {e}")
            raise TutorException(e, sys)
