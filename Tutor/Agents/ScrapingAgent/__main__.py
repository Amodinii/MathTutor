import logging
import click
import httpx
import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore, InMemoryPushNotifier
from a2a.types import AgentCapabilities, AgentCard, AgentSkill
from Tutor.Agents.ScrapingAgent.agent_executor import ScrapingAgentExecutor
from Tutor.Logging.Logger import logger


@click.command()
@click.option('--host', 'host', default='localhost')
@click.option('--port', 'port', default=10000)
def main(host, port):
    """Starts the Scraping Agent server."""
    try:
        # Define agent metadata
        capabilities = AgentCapabilities(
            streaming=True,
            pushNotifications=True,
        )

        # Define agent skill
        skill = AgentSkill(
            id='extract_questions',
            name='Web Scraping Question Extractor',
            description='Scrapes pages and extracts math questions using LLM',
            tags=['web scraping', 'question extraction', 'math'],
            examples=['Extract questions from these math resource pages.'],
        )

        # Define agent card
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

        # Build HTTP handler and server
        httpx_client = httpx.AsyncClient()
        request_handler = DefaultRequestHandler(
            agent_executor=ScrapingAgentExecutor(),
            task_store=InMemoryTaskStore(),
            push_notifier=InMemoryPushNotifier(httpx_client),
        )

        server = A2AStarletteApplication(
            agent_card=agent_card,
            http_handler=request_handler,
        )

        uvicorn.run(server.build(), host=host, port=port, timeout_keep_alive=300,timeout_graceful_shutdown=300)

    except Exception as e:
        logger.error(f'An error occurred during server startup: {e}')
        exit(1)


if __name__ == '__main__':
    main()