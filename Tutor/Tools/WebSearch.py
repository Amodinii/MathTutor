import sys
from langchain_tavily import TavilySearch
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

class WebSearch:
    def __init__(self, max_results: int):
        try:
            self.searchtool = TavilySearch(
                max_results=max_results,
                topic = "general"
            )
            logger.info("Web search initialized successfully.")
        except Exception as e:
            logger.error("Error initializing web search.")
            raise TutorException(e, sys)
    
    def search(self, query: str):
        try:
            response = self.searchtool.invoke({"query": query})
            logger.info(f"Web search completed for query: {query}")
            return response
        except Exception as e:
            logger.error("Error during web search.")
            raise TutorException(e, sys)