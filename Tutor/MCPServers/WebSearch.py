'''
This file is essentially used to create a MCP server that provides our WebSearch service.
'''
import sys
from mcp.server.fastmcp import FastMCP
from Tutor.Tools.WebSearch import WebSearch
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

class WebSearchServer:
    def __init__(self, max_results: int = 3):
        try:
            self.search_tool = WebSearch(max_results=max_results)
            self.mcp = FastMCP("web-search")
            logger.info(f" [WebSearch MCP Server] WebSearch MCP Server initialized with max_results: {max_results}")
        except TutorException as e:
            logger.error(f" [WebSearch MCP Server] Failed to initialize WebSearch MCP Server")
            raise TutorException(e, sys)

        @self.mcp.tool
        def search(query: str):
            """
            Perform a web search using the provided query string.

            Args:
                query: The search keyword or question.

            Returns:
                A list of search results with snippets and URLs.
            """
            try:
                if not query:
                    raise TutorException("Query cannot be empty", sys)

                logger.info(f"[WebSearch MCP Server] Searching for query: {query}")
                return self.search_tool.search(query=query)
            except TutorException as e:
                logger.error(f"[WebSearch MCP Server] Error occurred while searching: {e}")
                raise TutorException(e, sys)
        
    def serve(self):
        try:
            logger.info(" [WebSearch MCP Server] Starting WebSearch MCP Server...")
            self.mcp.serve()
        except TutorException as e:
            logger.error(f" [WebSearch MCP Server] Failed to start WebSearch MCP Server")
            raise TutorException(e, sys)