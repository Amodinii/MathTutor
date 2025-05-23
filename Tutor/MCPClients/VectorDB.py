import sys
from mcp import Client
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

class VectorDBClient:
    def __init__(self, server_url: str = "http://localhost:5000"):
        try:
            logger.info(f"[VectorDB Client] Initializing VectorDB Client with server URL: {server_url}")
            self.client = Client(server_url)
            self.retrieve_tool = self.client.tool("retrieve_documents")
        except TutorException as e:
            logger.error(f"[VectorDB Client] Failed to initialize VectorDB Client")
            raise TutorException(e, sys)

    def retrieve_documents(self, query: str, threshold: float = 0.5, num_results: int = 5):
        try:
            logger.info(f"[VectorDB Client] Retrieving documents for query: {query} with threshold: {threshold} and num_results: {num_results}")
            return self.retrieve_tool.invoke({
                "query": query,
                "threshold": threshold,
                "num_results": num_results
            })
        except TutorException as e:
            logger.error(f"[VectorDB Client] Error occurred while retrieving documents: {e}")
            raise TutorException(e, sys)