import sys
import asyncio
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException


class WebScrapeClient:
    def __init__(self, script_path: str = "Tutor/MCPServers/WebScrape.py"):
        self.script_path = str(Path(script_path).resolve())
        self.session = None
        self._task = None
        self._session_ready = asyncio.Event()

    async def connect(self):
        if not Path(self.script_path).exists():
            raise TutorException(f"[WebScrapeClient] Server script not found: {self.script_path}", sys)
        logger.info(f"[WebScrapeClient] Server script found: {self.script_path}")
        logger.info("[WebScrapeClient] Initializing WebScrape MCP Client...")

        self._task = asyncio.create_task(self._run())
        await self._session_ready.wait()

    async def _run(self):
        try:
            project_root = str(Path(__file__).resolve().parent.parent.parent)
            server_params = StdioServerParameters(command="python", args=[self.script_path], cwd=project_root)

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    logger.info("[WebScrapeClient] Client session created successfully.")
                    await session.initialize()
                    logger.info("[WebScrapeClient] Connected successfully.")

                    tools = (await session.list_tools()).tools
                    logger.info("[WebScrapeClient] Connected with tools: %s", [tool.name for tool in tools])

                    self.session = session
                    self._session_ready.set()

                    # Keep the session alive
                    await asyncio.Event().wait()

        except asyncio.CancelledError:
            logger.info("[WebScrapeClient] Shutdown requested.")
        except Exception as e:
            logger.error(f"[WebScrapeClient] MCP client error: {e}")
            self._session_ready.set()


    async def scrape(self, url: str):
        if not self.session:
            raise TutorException("[WebScrapeClient] Client not connected. Call connect() first.", sys)
        try:
            logger.info(f"[WebScrapeClient] Scraping URL: {url}")
            result = await self.session.call_tool("scrape_info", {"url": url})
            logger.info("[WebScrapeClient] Scraping completed.")
            return result
        except Exception as e:
            logger.error(f"[WebScrapeClient] Error during web scraping: {e}")
            raise TutorException(e, sys)

    async def close(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[WebScrapeClient] Closed.")