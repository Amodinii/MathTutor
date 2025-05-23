'''
This file is essentially used to create a MCP server that provides our WebSearch service.
'''
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from mcp.server.fastmcp import FastMCP
from Tutor.Tools.WebSearch import WebSearch
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("[WebSearchClient] Environment variables loaded from .env")
except ImportError:
    logger.info("[WebSearchClient] python-dotenv not available, using system env vars")

class WebSearchServer:
    def __init__(self, max_results: int = 3):
        try:
            logger.info("Initializing WebSearch MCP Server...")
            logger.info("Creating WebSearch instance...")
            logger.info(f"TAVILY_API_KEY exists: {'TAVILY_API_KEY' in os.environ}")
            self.search_tool = WebSearch(max_results=max_results)
            logger.info("WebSearch instance created successfully.")
            logger.info("Creating FastMCP instance...")
            self.mcp = FastMCP("web-search")
            logger.info("FastMCP instance created successfully.")
            logger.info(f" [WebSearch MCP Server] WebSearch MCP Server initialized with max_results: {max_results}")
        except TutorException as e:
            logger.error(f" [WebSearch MCP Server] Failed to initialize WebSearch MCP Server")
            raise TutorException(e, sys)

        @self.mcp.tool()
        def search(query: str):
            """
            Perform a web search using the provided query string.

            Args:
                query: The search keyword or question.

            Returns:
                A list of search results with snippets and URLs.
            """
            try:
                logger.info(f"[WebSearch MCP Server] Searching for query: {query}")
                return self.search_tool.search(query=query)
            except TutorException as e:
                logger.error(f"[WebSearch MCP Server] Error occurred while searching: {e}")
                raise TutorException(e, sys)
        
    def serve(self):
        try:
            logger.info(" [WebSearch MCP Server] Starting WebSearch MCP Server...")
            self.mcp.run(transport='stdio')
        except TutorException as e:
            logger.error(f" [WebSearch MCP Server] Failed to start WebSearch MCP Server")
            raise TutorException(e, sys)
    
def main():
    logger.info("main() function of web search server called")
    server = WebSearchServer()
    logger.info("WebSearchServer instance created")
    server.serve()

if __name__ == "__main__":
    main()