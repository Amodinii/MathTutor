from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from Tutor.Agents.TeachingAgent.agent_executor import TeachingAgentExecutor
from Tutor.Agents.TeachingAgent.card import agent_card

from starlette.responses import JSONResponse, HTMLResponse
from starlette.routing import Route
import uvicorn
import platform

# Health check endpoint at "/"
def healthcheck(request):
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <title>Teaching Agent</title>
    </head>
    <body style="font-family: sans-serif; padding: 2rem;">
        <h1> Teaching Agent is Running</h1>
        <p>You’ve reached the Teaching Agent root endpoint.</p>
        <p>Try <a href="/status">/status</a> for a JSON response about the teaching agent's status. </p>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)

# Status endpoint at "/status"
def status(request):
    return JSONResponse({
        "status": "ready",
        "agent": "Teaching Agent",
        "version": "v1.0.0",
        "python": platform.python_version()
    })

if __name__ == "__main__":
    # Step 1: Initialize the agent executor and task store
    request_handler = DefaultRequestHandler(
        agent_executor=TeachingAgentExecutor(),
        task_store=InMemoryTaskStore()
    )

    # Step 2: Build the Starlette app
    app_builder = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

    # Step 3: Add custom routes for health/status checks
    app = app_builder.build()
    app.router.routes.append(Route("/", healthcheck, methods=["GET"]))
    app.router.routes.append(Route("/status", status, methods=["GET"]))

    # Step 4: Run with Uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9001)