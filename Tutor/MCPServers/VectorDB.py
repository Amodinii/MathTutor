'''
This file is essentially used to create a MCP server that provides our VectorDB service.
'''
import sys
from mcp.server.fastmcp import FastMCP
from Tutor.Services.VectorStore import VectorStore
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

class VectorDBServer:
    def __init__(self, model_name: str):
        try:
            self.store = VectorStore(model_name=model_name)
            self.mcp = FastMCP("vector-db")
            logger.info(f" [VectorDB MCP Server] VectorDB MCP Server initialized with model: {model_name}")
        except TutorException as e:
            logger.error(f" [VectorDB MCP Server] Failed to initialize VectorDB MCP Server")
            raise TutorException(e, sys)

        @self.mcp.tool
        def retrieve_documents(query: str, threshold: float = 0.5, num_results: int = 5):
            """
            Retrieve relevant documents from the vector store using similarity search.

            Args:
                query: The user question or prompt.
                threshold: Minimum similarity score (0 to 1).
                num_results: Maximum number of documents to return.

            Returns:
                A list of matching documents.
            """
            try:
                if not query:
                    raise TutorException("Query cannot be empty", sys)

                logger.info(f"[VectorDB MCP Server] Retrieving documents for query: {query} with threshold: {threshold} and num_results: {num_results}")
                return self.store.retrieve(query, threshold, num_results)
            except TutorException as e:
                logger.error(f"[VectorDB MCP Server] Error occurred while retrieving documents: {e}")
                raise TutorException(e, sys)

    def serve(self):
        try:
            logger.info(" [VectorDB MCP Server] Starting VectorDB MCP Server...")
            self.mcp.serve()
        except TutorException as e:
            logger.error(f" [VectorDB MCP Server] Failed to start VectorDB MCP Server")
            raise TutorException(e, sys)