import uvicorn
from starlette.responses import JSONResponse, HTMLResponse
from starlette.requests import Request
from starlette.routing import Route

from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from Tutor.Agents.ReasoningAgent.agent_executor import ReasoningAgentExecutor
from Tutor.Agents.ReasoningAgent.card import agent_card


def healthcheck(request: Request):
    return JSONResponse({"status": "ok", "message": "Reasoning Agent is live"})

def root_check(request: Request):
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8" />
        <title>Reasoning Agent</title>
    </head>
    <body style="font-family: sans-serif; padding: 2rem;">
        <h1> Reasoning Agent is Running</h1>
        <p>You’ve reached the Reasoning Agent root endpoint.</p>
        <p>Try <a href="/status">/status</a> for a JSON response about the Reasoning agent's status. </p>
    </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=200)


if __name__ == "__main__":
    # 1) Create the A2A request handler with your executor
    handler = DefaultRequestHandler(
        agent_executor=ReasoningAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # 2) Build the A2A Starlette app using your AgentCard
    app_builder = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=handler
    )
    app = app_builder.build()

    # 3) Add / and /status routes
    app.routes.append(Route("/", endpoint=root_check, methods=["GET"]))
    app.routes.append(Route("/status", endpoint=healthcheck, methods=["GET"]))

    # 4) Run the server
    uvicorn.run(app, host="0.0.0.0", port=9002)
