from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils import new_agent_text_message

from Tutor.Agents.TeachingAgent.card import simplify_skill
from Tutor.Agents.TeachingAgent.Teaching import run_teaching


class TeachingAgentExecutor(AgentExecutor):
    """
    Implements the A2A Executor interface:
      - execute() is called for both message/send and message/stream.
      - cancel() is called on cancellation.
    """

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        # 1) Validate the skill
        if context.skill_id != simplify_skill.id:
            event_queue.enqueue_event(
                new_agent_text_message(f"Unknown skill_id {context.skill_id}")
            )
            return

        # 2) Run your LangGraph teaching loop
        try:
            final_state = await run_teaching(context.input)
            msg = final_state["improved_explanation"]
            event_queue.enqueue_event(new_agent_text_message(msg))
        except Exception as e:
            event_queue.enqueue_event(new_agent_text_message(f"[error] {e}"))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        # Optional: support cancellation if you want
        raise NotImplementedError("Cancellation not supported.")