import sys
import asyncio
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException


class WebSearchClient:
    def __init__(self, script_path: str = "Tutor/MCPServers/WebSearch.py"):
        self.script_path = str(Path(script_path).resolve())
        self.session = None
        self._task = None
        self._session_ready = asyncio.Event()

    async def connect(self):
        if not Path(self.script_path).exists():
            raise TutorException(f"Server script not found: {self.script_path}", sys)

        logger.info(f"[WebSearchClient] Server script found: {self.script_path}")
        logger.info("[WebSearchClient] Initializing WebSearch MCP Client...")

        self._task = asyncio.create_task(self._run())
        await self._session_ready.wait()

    async def _run(self):
        try:
            project_root = str(Path(__file__).resolve().parent.parent.parent)
            server_params = StdioServerParameters(command="python", args=[self.script_path], cwd=project_root)

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    logger.info("[WebSearchClient] Client session created successfully.")
                    await session.initialize()
                    logger.info("[WebSearchClient] Connected successfully.")
                    
                    self.session = session
                    self._session_ready.set()

                    await asyncio.Future()  # Block forever
        except asyncio.CancelledError:
            logger.info("[WebSearchClient] Shutdown requested.")
        except Exception as e:
            logger.error(f"[WebSearchClient] MCP client error: {e}")
            self._session_ready.set()

    async def search(self, query: str):
        if not self.session:
            raise TutorException("Client not connected. Call connect() first.", sys)

        try:
            logger.info(f"[WebSearchClient] Performing web search for query: {query}")
            result = await self.session.call_tool("search", {"query": query})
            return result
        except Exception as e:
            logger.error(f"[WebSearchClient] Error during web search: {e}")
            raise TutorException(e, sys)

    async def close(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[WebSearchClient] Closed.")