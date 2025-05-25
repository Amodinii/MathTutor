from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException
from Tutor.Agents.ReasoningAgent.card import solve_skill
from Tutor.Agents.ReasoningAgent.Reasoning import run_reasoning
import httpx

TEACHING_AGENT_URL = "http://localhost:9001/tasks"

class ReasoningAgentExecutor(AgentExecutor):
    def __init__(self):
        pass  # If you want, you can keep state here

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            inp = context.input

            # 1) LangGraph reasoning
            result = await run_reasoning(inp)
            answer = result["answer"]
            explanation = result["explanation"]

            # 2) Call Teaching Agent
            teach_payload = {
                "skill_id": "simplify_explanation",
                "input": {
                    "question": inp["question"],
                    "answer": answer,
                    "explanation": explanation,
                    "feedback_history": [],
                    "thread_id": inp.get("thread_id"),
                }
            }

            async with httpx.AsyncClient() as client:
                resp = await client.post(TEACHING_AGENT_URL, json=teach_payload)
                resp.raise_for_status()
                teach_out = resp.json().get("output", {})

            simplified = teach_out.get("improved_explanation") or teach_out.get("simplified_explanation")
            response_text = f"Answer: {answer}\nExplanation: {simplified}"

            event_queue.enqueue_event(new_agent_text_message(response_text))

        except Exception as e:
            logger.error(f"[ReasoningAgent] A2A execution failed: {e}")
            event_queue.enqueue_event(new_agent_text_message(f"[error] {e}"))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception("Cancel not supported")