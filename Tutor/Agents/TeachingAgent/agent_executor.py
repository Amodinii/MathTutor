import ast
import asyncio
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types import (
    InternalError,
    InvalidParamsError,
    Task,
    TaskState,
    TextPart,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError

from Tutor.Agents.TeachingAgent.Teaching import run_teaching
from Tutor.Logging.Logger import logger
from typing_extensions import override


class TeachingAgentExecutor(AgentExecutor):
    """A2A-compliant executor for the Teaching Agent."""

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        try:
            # Step 1: Parse user input
            raw_input = context.get_user_input()
            logger.info("[TeachingAgentExecutor] Raw input: %s", raw_input)
            try:
                user_input = ast.literal_eval(raw_input)
            except Exception as e:
                logger.error("[TeachingAgentExecutor] Failed to parse input: %s", e)
                raise ServerError(error=InvalidParamsError())

            # Step 2: Get or create task
            task = context.current_task
            if not task:
                task = new_task(context.message)
                event_queue.enqueue_event(task)

            updater = TaskUpdater(event_queue, task.id, task.contextId)

            # Step 3: Progress - starting
            updater.update_status(
                TaskState.working,
                new_agent_text_message("Simplifying explanation...", task.contextId, task.id),
            )

            await asyncio.sleep(0.1)  # Brief pause for UX

            # Step 4: Run teaching model
            logger.info("[TeachingAgentExecutor] Running teaching model.")
            final_state = await run_teaching(user_input)
            improved_explanation = final_state.get("improved_explanation", "[no explanation generated]")
            # Step 5: Add explanation as artifact
            updater.add_artifact(
                parts=[TextPart(text=improved_explanation)],
                name="teaching_result",
            )

            # Step 6: Mark task complete
            updater.update_status(
                TaskState.completed,
                new_agent_text_message("Explanation simplified successfully.", task.contextId, task.id),
                final=True,
            )

            logger.info("[TeachingAgentExecutor] Task %s completed.", task.id)

        except Exception as e:
            logger.exception("[TeachingAgentExecutor] Execution failed.")
            if 'updater' in locals():
                updater.update_status(
                    TaskState.failed,
                    new_agent_text_message(f"Failed to simplify explanation: {str(e)}", task.contextId, task.id),
                    final=True,
                )
            raise ServerError(error=InternalError()) from e

    @override
    async def cancel(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> Task | None:
        task = context.current_task
        if task:
            updater = TaskUpdater(event_queue, task.id, task.contextId)
            updater.update_status(
                TaskState.cancelled,
                new_agent_text_message("Teaching job was cancelled.", task.contextId, task.id),
                final=True,
            )
            logger.info("[TeachingAgentExecutor] Task %s cancelled.", task.id)
            return task
        return None