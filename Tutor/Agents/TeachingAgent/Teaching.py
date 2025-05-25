import sys
import asyncio
from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException
from Tutor.Services.TeachingModel import TeachingModel

# ——— State Schema ———
class TeachingState(TypedDict):
    question: str
    answer: str
    explanation: str
    feedback_history: List[str]
    thread_id: Optional[str]
    improved_explanation: Optional[str]
    user_done: Optional[bool]

# ——— Initialize Model ———
model = TeachingModel(model_name="llama3-70b-8192")

# ——— Node: Simplify Explanation ———
async def simplify_node(state: TeachingState) -> TeachingState:
    try:
        logger.info("[TeachingAgent] simplify_node running...")
        improved = await model.explain(
            question=state["question"],
            answer=state["answer"],
            explanation=state["explanation"],
            feedback_history=state["feedback_history"],
            thread_id=state["thread_id"]
        )
        return {**state, "improved_explanation": improved}
    except Exception as e:
        raise TutorException(e, sys)

# ——— Node: Gather User Doubt ———
async def feedback_node(state: TeachingState) -> TeachingState:
    # If this came over A2A (via HTTP), just end the loop immediately.
    # We assume thread_id is always set for HTTP calls.
    if state.get("thread_id"):
        return { **state, "user_done": True }

    # Otherwise (local CLI), prompt the user:
    print("\nCurrent Explanation:\n", state["improved_explanation"])
    user_input = input("\nAny more doubts? Type 'done' to finish or ask: ").strip()
    done = user_input.lower() == "done"
    history = state["feedback_history"] + ([] if done else [user_input])
    return { **state, "feedback_history": history, "user_done": done }

# ——— Router: Continue or End ———
def router(state: TeachingState) -> str:
    return END if state.get("user_done") else "simplify"

# ——— Build LangGraph ———
graph = StateGraph(TeachingState)
graph.add_node("simplify", simplify_node)
graph.add_node("feedback", feedback_node)
graph.set_entry_point("simplify")
graph.add_edge("simplify", "feedback")
graph.add_conditional_edges("feedback", router)
app_runnable = graph.compile()

# ——— Public API ———
async def run_teaching(input_data: dict) -> dict:
    """
    input_data must contain:
      question, answer, explanation, feedback_history (list), thread_id (opt)
    """
    try:
        initial_state: TeachingState = {
            "question": input_data["question"],
            "answer": input_data["answer"],
            "explanation": input_data["explanation"],
            "feedback_history": input_data.get("feedback_history", []),
            "thread_id": input_data.get("thread_id"),
            "improved_explanation": None,
            "user_done": False
        }
        final_state = await app_runnable.ainvoke(initial_state, config=RunnableConfig())
        return final_state  # contains improved_explanation and updated feedback_history
    except Exception as e:
        raise TutorException(e, sys)
