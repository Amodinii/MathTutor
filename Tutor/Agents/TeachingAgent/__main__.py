from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from Tutor.Agents.TeachingAgent.agent_executor import TeachingAgentExecutor
from Tutor.Agents.TeachingAgent.card import agent_card
import uvicorn

if __name__ == "__main__":
    # Step 1: Handler with Executor and Task Store
    request_handler = DefaultRequestHandler(
        agent_executor=TeachingAgentExecutor(),
        task_store=InMemoryTaskStore()
    )

    # Step 2: Starlette App Builder
    app_builder = A2AStarletteApplication(
        agent_card=agent_card,
        http_handler=request_handler
    )

    # Step 3: Start Server
    uvicorn.run(app_builder.build(), host="0.0.0.0", port=9001)
