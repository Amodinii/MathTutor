'''
This file is essentially used to create a MCP server that provides our VectorDB service.
'''
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from mcp.server.fastmcp import FastMCP
from Tutor.Services.VectorStore import VectorStore
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

class VectorDBServer:
    def __init__(self):
        try:
            logger.info("Initializing VectorDB MCP Server...")
            logger.info("Creating VectorStore instance...")
            self.store = VectorStore(model_name="sentence-transformers/all-MiniLM-L6-v2")
            logger.info("VectorStore instance created successfully.")
            logger.info("Creating FastMCP instance...")
            self.mcp = FastMCP("vector-db")
            logger.info("FastMCP instance created successfully.")
            logger.info(f" [VectorDB MCP Server] VectorDB MCP Server initialized with model: sentence-transformers/all-MiniLM-L6-v2")
        except TutorException as e:
            logger.error(f" [VectorDB MCP Server] Failed to initialize VectorDB MCP Server")
            raise TutorException(e, sys)

        @self.mcp.tool()
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
            self.mcp.run(transport='stdio')
        except TutorException as e:
            logger.error(f" [VectorDB MCP Server] Failed to start VectorDB MCP Server")
            raise TutorException(e, sys)

def main():
    logger.info("main() function of vector db server called")
    server = VectorDBServer()
    logger.info("VectorDBServer instance created")
    server.serve()


if __name__ == "__main__":
    main()