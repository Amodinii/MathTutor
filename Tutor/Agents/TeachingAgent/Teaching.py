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
        return {**state, "improved_explanation": improved, "user_done": True}
    except Exception as e:
        raise TutorException(e, sys)

# ——— Build LangGraph ———
graph = StateGraph(TeachingState)
graph.add_node("simplify", simplify_node)
graph.set_entry_point("simplify")
graph.add_edge("simplify", END)
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
        return final_state  # contains improved_explanation
    except Exception as e:
        raise TutorException(e, sys)
