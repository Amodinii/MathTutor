import ast
import json
import httpx
import os
from datetime import datetime
from uuid import uuid4
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import InternalError, TaskState, TextPart
from a2a.utils import new_agent_text_message, new_task
from a2a.utils.errors import ServerError
from Tutor.Logging.Logger import logger
from Tutor.Agents.ReasoningAgent.Reasoning import build_reasoning_agent

TEACHING_AGENT_URL = "http://localhost:9001"
SIMPLIFY_SKILL_ID = "simplify_explanation"

def save_response_artifacts(response_text: str):
    final_dir = "Tutor/Agents/TeachingAgent/response"
    os.makedirs(final_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_txt_filename = f"simplified_explanation_{timestamp}.txt"
    final_txt_path = os.path.join(final_dir, final_txt_filename)

    try:
        with open(final_txt_path, "w", encoding="utf-8") as f_txt:
            f_txt.write(response_text.strip())
        logger.info(f"[A2A Client Teaching] Simplified explanation saved as TXT: {final_txt_path}")
        print(f"[A2A Client Teaching] Simplified Explanation:\n{response_text}")
    except Exception as e:
        logger.exception(f"[A2A Client Teaching] Failed to save explanation: {e}")

class ReasoningAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = None

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

            # Step 3: Call Teaching Agent
            payload_query = {
                "question": question,
                "answer": answer,
                "explanation": explanation,
                "feedback_history": [],
                "thread_id": input_data.get("thread_id"),
            }

            teach_payload = {
                "skill": SIMPLIFY_SKILL_ID,
                "message": {
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": str(payload_query),
                        }
                    ],
                    "messageId": uuid4().hex,
                }
            }

            try:
                async with httpx.AsyncClient() as client:
                    logger.info("[ReasoningAgentExecutor] Requesting simplification from Teaching Agent.")
                    response = await client.post(
                    TEACHING_AGENT_URL,
                    json={"skill": SIMPLIFY_SKILL_ID,**teach_payload},
                )
                    print("Obtained Response")
                    print(response)
                    response.raise_for_status()
                    simplified = response.json().get("output", "")
                    save_response_artifacts(response_text=simplified)
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