import sys
import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

class WebSearchClient:
    def __init__(self, script_path: str = "Tutor/MCPServers/WebSearch.py"):
        self.script_path = script_path
        self.exit_stack = AsyncExitStack()
        self.session = None

    async def connect(self):
        try:
            logger.info(f"[WebSearchClient] Connecting to MCP server via stdio: {self.script_path}")
            server_params = StdioServerParameters(command="python", args=[self.script_path])
            transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.write = transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
            await self.session.initialize()
            logger.info("[WebSearchClient] Connected successfully.")
        except Exception as e:
            logger.error(f"[WebSearchClient] Failed to connect: {e}")
            raise TutorException(e, sys)

    async def search(self, query: str):
        try:
            if not self.session:
                raise TutorException("Client not connected. Call connect() first.", sys)
                
            logger.info(f"[WebSearchClient] Performing web search for query: {query}")
            result = await self.session.call_tool("search", {"query": query})
            return result
        except Exception as e:
            logger.error(f"[WebSearchClient] Error during web search: {e}")
            raise TutorException(e, sys)

    async def close(self):
        await self.exit_stack.aclose()