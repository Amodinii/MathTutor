import sys
import asyncio
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException


class VectorDBClient:
    def __init__(self, script_path: str = "Tutor/MCPServers/VectorDB.py"):
        self.script_path = str(Path(script_path).resolve())
        self.session = None
        self._task = None
        self._session_ready = asyncio.Event()

    async def connect(self):
        if not Path(self.script_path).exists():
            raise TutorException(f"Server script not found: {self.script_path}", sys)

        logger.info(f"[VectorDBClient] Server script found: {self.script_path}")
        logger.info("[VectorDBClient] Initializing VectorDB MCP Client...")

        self._task = asyncio.create_task(self._run())

        # Wait until session is initialized
        await self._session_ready.wait()

    async def _run(self):
        try:
            project_root = str(Path(__file__).resolve().parent.parent.parent)
            server_params = StdioServerParameters(command="python", args=[self.script_path], cwd=project_root)

            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    logger.info("[VectorDBClient] Client session created successfully.")
                    await session.initialize()
                    tools = (await session.list_tools()).tools
                    logger.info("[VectorDBClient] Connected with tools: %s", [tool.name for tool in tools])

                    self.session = session
                    self._session_ready.set()

                    await asyncio.Future()  # Block forever until cancelled
        except asyncio.CancelledError:
            logger.info("[VectorDBClient] Shutdown requested.")
        except Exception as e:
            logger.error(f"[VectorDBClient] MCP client error: {e}")
            self._session_ready.set()  # Unblock connect even if failed

    async def retrieve_documents(self, query: str, threshold: float = 0.5, num_results: int = 5):
        if not self.session:
            raise TutorException("Client not connected. Call connect() first.", sys)

        logger.info(f"[VectorDBClient] Retrieving documents for query: {query}")
        try:
            result = await self.session.call_tool("retrieve_documents", {
                "query": query,
                "threshold": threshold,
                "num_results": num_results
            })
            return result
        except Exception as e:
            logger.error(f"[VectorDBClient] Error retrieving documents: {e}")
            raise TutorException(e, sys)

    async def close(self):
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("[VectorDBClient] Closed.")