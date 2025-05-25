import uvicorn
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore

from Tutor.Agents.ReasoningAgent.agent_executor import ReasoningAgentExecutor
from Tutor.Agents.ReasoningAgent.card import agent_card

if __name__ == "__main__":
    # 1) Create the A2A request handler with your executor
    handler = DefaultRequestHandler(
        agent_executor=ReasoningAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    # 2) Build the A2A Starlette app using your AgentCard
    server_app = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=handler
    ).build()

    # 3) Run it
    uvicorn.run(server_app, host="0.0.0.0", port=9002)
