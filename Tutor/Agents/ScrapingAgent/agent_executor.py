import json
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
    UnsupportedOperationError,
)
from a2a.utils import (
    new_agent_text_message,
    new_task,
)
from a2a.utils.errors import ServerError

from Tutor.Agents.ScrapingAgent.Agent import build_scraping_agent
from Tutor.Logging.Logger import logger
from typing_extensions import override

class ScrapingAgentExecutor(AgentExecutor):
    """A2A-compatible executor for the ScrapingAgent with progress updates."""
    
    def __init__(self):
        self.agent = None

    @override
    async def execute(
        self,
        context: RequestContext,
        event_queue: EventQueue,
    ) -> None:
        try:
            # Initialize agent if needed
            if not self.agent:
                logger.info("[ScrapingAgentExecutor] Initializing agent.")
                self.agent = await build_scraping_agent()

            # Parse input
            input_data = self._parse_input(context.get_user_input())
            
            # Get or create task
            task = context.current_task
            if not task:
                task = new_task(context.message)
                event_queue.enqueue_event(task)

            updater = TaskUpdater(event_queue, task.id, task.contextId)
            
            # Step 1: Immediate acknowledgment
            updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    f"Starting scraping job for {len(input_data) if isinstance(input_data, list) else 1} URL(s)...",
                    task.contextId, 
                    task.id
                ),
            )

            # Step 2: Progress update - starting scraping
            await asyncio.sleep(0.1)  # Small delay to ensure message is sent
            updater.update_status(
                TaskState.working,
                new_agent_text_message(
                    "Fetching web content and analyzing pages...",
                    task.contextId, 
                    task.id
                ),
            )

            # Step 3: Do the actual scraping (this is the long operation)
            logger.info("[ScrapingAgentExecutor] Running scraping agent.")
            
            # Create a task to monitor progress
            scraping_task = asyncio.create_task(self.agent(input_data))
            
            # Wait for completion with periodic progress updates
            extracted = await self._wait_with_progress_updates(
                scraping_task, updater, task
            )

            # Step 4: Final success message and artifact
            message_text = f"Scraping completed successfully! Extracted {len(extracted)} structured question(s)."
            
            updater.add_artifact(
                [TextPart(text=json.dumps(extracted, indent=2))],
                name="scraped_questions",
            )
            
            updater.update_status(
                TaskState.completed,
                new_agent_text_message(message_text, task.contextId, task.id),
                final=True,
            )

            logger.info(f"[ScrapingAgentExecutor] Task {task.id} completed successfully")

        except Exception as e:
            logger.exception("[ScrapingAgentExecutor] Failed during execution.")
            if 'updater' in locals():
                updater.update_status(
                    TaskState.failed,
                    new_agent_text_message(
                        f"❌ Scraping failed: {str(e)[:100]}",
                        task.contextId, 
                        task.id
                    ),
                    final=True,
                )
            raise ServerError(error=InternalError()) from e

    async def _wait_with_progress_updates(
        self, 
        scraping_task: asyncio.Task, 
        updater: TaskUpdater, 
        task: Task
    ):
        """Wait for scraping task with periodic progress updates."""
        
        progress_messages = [
            "Analyzing page structure...",
            "Processing content with AI...",
            "Extracting question patterns...",
            "Identifying answer formats...",
            "Structuring extracted data...",
        ]
        
        message_index = 0
        update_interval = 15  # seconds
        
        while not scraping_task.done():
            try:
                # Wait for either completion or timeout
                result = await asyncio.wait_for(
                    asyncio.shield(scraping_task), 
                    timeout=update_interval
                )
                return result
                
            except asyncio.TimeoutError:
                # Task is still running, send progress update
                if message_index < len(progress_messages):
                    updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            progress_messages[message_index],
                            task.contextId, 
                            task.id
                        ),
                    )
                    message_index += 1
                else:
                    # Cycle through messages or show elapsed time
                    elapsed_minutes = (message_index - len(progress_messages) + 1) * (update_interval / 60)
                    updater.update_status(
                        TaskState.working,
                        new_agent_text_message(
                            f"Still processing... ({elapsed_minutes:.1f} minutes elapsed)",
                            task.contextId, 
                            task.id
                        ),
                    )
                    message_index += 1
                
                continue
        
        # Task completed
        return await scraping_task

    def _parse_input(self, user_input: str):
        """Parse and validate user input."""
        try:
            input_data = ast.literal_eval(user_input)
            logger.info("[ScrapingAgentExecutor] Input type is %s.", type(input_data))

            if isinstance(input_data, str):
                try:
                    logger.info("[ScrapingAgentExecutor] Attempting to parse input as JSON.")
                    input_data = json.loads(input_data)
                    logger.info("[ScrapingAgentExecutor] Input parsed as JSON.")
                except json.JSONDecodeError:
                    raise ServerError(error=InvalidParamsError())
            
            return input_data
            
        except Exception as e:
            logger.error(f"[ScrapingAgentExecutor] Input parsing failed: {e}")
            raise ServerError(error=InvalidParamsError()) from e

    @override
    async def cancel(
        self, context: RequestContext, event_queue: EventQueue
    ) -> Task | None:
        """Handle cancellation requests."""
        task = context.current_task
        if task:
            updater = TaskUpdater(event_queue, task.id, task.contextId)
            updater.update_status(
                TaskState.cancelled,
                new_agent_text_message(
                    "Scraping job cancelled by user.",
                    task.contextId, 
                    task.id
                ),
                final=True,
            )
            logger.info(f"[ScrapingAgentExecutor] Task {task.id} marked as cancelled")
            return task
        
        return None