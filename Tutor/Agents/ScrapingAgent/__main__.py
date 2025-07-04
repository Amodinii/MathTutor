import os
from urllib.parse import urlparse
import click
import httpx
import uvicorn
import platform

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, InMemoryPushNotifier
from a2a.types import AgentCapabilities, AgentCard, AgentSkill

from Tutor.Agents.ScrapingAgent.agent_executor import ScrapingAgentExecutor
from Tutor.Logging.Logger import logger

from starlette.responses import JSONResponse, HTMLResponse
from starlette.routing import Route

# Health check endpoint at "/"
def healthcheck(request):
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <title>Scraping Agent</title>
    </head>
    <body style="font-family: sans-serif; padding: 2rem;">
        <h1> Scraping Agent is Running</h1>
        <p>You’ve reached the Scraping Agent root endpoint.</p>
        <p>Try <a href="/status">/status</a> for a JSON response about the scraping agent's status. </p>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)

# Status endpoint at "/status"
def status(request):
    return JSONResponse({
        "status": "ready",
        "agent": "Scraping Agent",
        "version": "v1.0.0",
        "python": platform.python_version()
    })

@click.command()
def main():
    """Starts the Scraping Agent server."""

    # Read from environment or fallback to default
    scraping_url = os.getenv("SCRAPING_AGENT_URL", "http://localhost:10000")
    parsed = urlparse(scraping_url)
    host = parsed.hostname or "localhost"
    port = parsed.port or 10000

    try:
        # Define agent metadata
        capabilities = AgentCapabilities(
            streaming=True,
            pushNotifications=True,
        )

        skill = AgentSkill(
            id='extract_questions',
            name='Web Scraping Question Extractor',
            description='Scrapes pages and extracts math questions using LLM',
            tags=['web scraping', 'question extraction', 'math'],
            examples=['Extract questions from these math resource pages.'],
        )

        agent_card = AgentCard(
            name='Scraping Agent',
            description='Extracts structured math questions from web pages using LLM.',
            url=f'http://{host}:{port}/',
            version='1.0.0',
            defaultInputModes=['text/markdown', 'text/plain'],
            defaultOutputModes=['application/json'],
            capabilities=capabilities,
            skills=[skill],
        )

        # Build HTTP handler and Starlette app
        httpx_client = httpx.AsyncClient()
        request_handler = DefaultRequestHandler(
            agent_executor=ScrapingAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_notifier=InMemoryPushNotifier(httpx_client),
        )

        app_builder = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        )

        app = app_builder.build()
        app.router.routes.append(Route("/", healthcheck, methods=["GET"]))
        app.router.routes.append(Route("/status", status, methods=["GET"]))

        uvicorn.run(app, host=host, port=port, timeout_keep_alive=300, timeout_graceful_shutdown=300)

    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)

if __name__ == '__main__':
    main()