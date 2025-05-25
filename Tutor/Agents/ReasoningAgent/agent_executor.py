import ast
import json
import httpx
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import InternalError, TaskState, TextPart
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError
from Tutor.Logging.Logger import logger
from Tutor.Agents.ReasoningAgent.Reasoning import build_reasoning_agent

TEACHING_AGENT_URL = "http://localhost:9001/tasks"
SIMPLIFY_SKILL_ID = "simplify_explanation"

class ReasoningAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = None  # We'll assign this on first execution

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        try:
            input_data = ast.literal_eval(context.get_user_input())
            logger.info("[ReasoningAgentExecutor] Received input: %s", input_data)

            task = context.current_task or new_task(context.message)
            event_queue.enqueue_event(task)
            updater = TaskUpdater(event_queue, task.id, task.contextId)

            updater.update_status(
                TaskState.working,
                new_agent_text_message("Running reasoning process...", task.contextId, task.id),
            )

            # Initialize agent on first run
            if self.agent is None:
                logger.info("[ReasoningAgentExecutor] Initializing reasoning agent.")
                self.agent = await build_reasoning_agent()

            question = input_data.get("question")
            if not question:
                raise ValueError("Missing 'question' in input.")

            logger.info("[ReasoningAgentExecutor] Calling reasoning agent.")
            result = await self.agent(question)
            parsed = json.loads(result.content.replace('\n', ' ').replace('\r', ' '))
            answer = parsed.get("correct_answer")
            explanation = parsed.get("reason")
            if not answer or not explanation:
                raise ValueError("Missing answer or explanation in result.")

            # Step 3: Simplify explanation (optional)
            teach_payload = {
                "skill_id": SIMPLIFY_SKILL_ID,
                "input": {
                    "question": question,
                    "answer": answer,
                    "explanation": explanation,
                    "feedback_history": [],
                    "thread_id": input_data.get("thread_id"),
                }
            }

            try:
                async with httpx.AsyncClient() as client:
                    logger.info("[ReasoningAgentExecutor] Requesting simplification from Teaching Agent.")
                    resp = await client.post(TEACHING_AGENT_URL, json=teach_payload)
                    resp.raise_for_status()
                    teach_out = resp.json().get("output", {})
                    simplified = teach_out.get("improved_explanation") or teach_out.get("simplified_explanation")
                    if simplified:
                        parsed["reason"] = simplified
            except Exception as te:
                logger.warning(f"[ReasoningAgentExecutor] Teaching Agent call failed: {te}")

            # Step 4: Add result artifact
            updater.add_artifact(
                parts=[TextPart(text=json.dumps(parsed, indent=2))],
                name="reasoning_result",
            )

            updater.update_status(
                TaskState.completed,
                new_agent_text_message("Reasoning completed successfully.", task.contextId, task.id),
                final=True,
            )

            logger.info(f"[ReasoningAgentExecutor] Task {task.id} completed successfully")

        except Exception as e:
            logger.exception("[ReasoningAgentExecutor] Execution failed.")
            if 'updater' in locals():
                updater.update_status(
                    TaskState.failed,
                    new_agent_text_message(f"Reasoning failed: {str(e)[:100]}", task.contextId, task.id),
                    final=True,
                )
            raise ServerError(error=InternalError()) from e

    async def cancel(self, context: RequestContext, event_queue: EventQueue):
        task = context.current_task
        if task:
            updater = TaskUpdater(event_queue, task.id, task.contextId)
            updater.update_status(
                TaskState.cancelled,
                new_agent_text_message("Reasoning task cancelled by user.", task.contextId, task.id),
                final=True,
            )
            logger.info(f"[ReasoningAgentExecutor] Task {task.id} marked as cancelled")
            return task
        return None