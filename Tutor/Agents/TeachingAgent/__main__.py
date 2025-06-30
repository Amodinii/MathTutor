from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from Tutor.Agents.TeachingAgent.agent_executor import TeachingAgentExecutor
from Tutor.Agents.TeachingAgent.card import agent_card

from starlette.responses import JSONResponse
from starlette.routing import Route
import uvicorn
import platform

# Health check endpoint at "/"
def healthcheck(request):
    return JSONResponse({
        "status": "ok",
        "message": "Teaching Agent is running"
    })

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