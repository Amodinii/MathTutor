import sys
import asyncio
from typing import TypedDict, Optional, List
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableConfig

from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException
from Tutor.Services.TeachingModel import TeachingModel


# Define the state schema
class TeachingState(TypedDict):
    question: str
    answer: str
    explanation: str
    feedback_history: List[str]
    thread_id: Optional[str]
    improved_explanation: Optional[str]
    user_done: Optional[bool]


# Initialize the model
model = TeachingModel(model_name="llama3-70b-8192")


# Node 1: Simplify explanation based on history
async def simplify_explanation(state: TeachingState) -> TeachingState:
    try:
        logger.info("Simplifying explanation...")
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


# Node 2: Ask user if they understood or have more doubts
async def get_user_feedback(state: TeachingState) -> TeachingState:
    try:
        print("\nUpdated Explanation:\n", state["improved_explanation"])
        user_input = input("\nAny doubts? Type 'done' to finish or enter your question: ").strip()
        is_done = user_input.lower() == "done"
        updated_history = state["feedback_history"] + ([user_input] if not is_done else [])
        return {**state, "feedback_history": updated_history, "user_done": is_done}
    except Exception as e:
        raise TutorException(e, sys)


# Router to decide if we should stop
def route(state: TeachingState) -> str:
    return END if state.get("user_done") else "simplify"


# Build the graph
graph = StateGraph(TeachingState)
graph.add_node("simplify", simplify_explanation)
graph.add_node("feedback", get_user_feedback)
graph.set_entry_point("simplify")
graph.add_edge("simplify", "feedback")
graph.add_conditional_edges("feedback", route)

app = graph.compile()


# TeachingAgent wrapper
class TeachingAgent:
    def __init__(self):
        self.app = app

    async def run(self, question, answer, explanation, thread_id=None):
        try:
            initial_state = {
                "question": question,
                "answer": answer,
                "explanation": explanation,
                "feedback_history": [],
                "thread_id": thread_id,
                "improved_explanation": None,
                "user_done": False
            }
            return await self.app.ainvoke(initial_state, config=RunnableConfig())
        except Exception as e:
            raise TutorException(e, sys)


# Test run
if __name__ == "__main__":
    async def test():
        agent = TeachingAgent()
        question = "How do you solve 2x + 3 = 7?"
        answer = "You subtract 3 from both sides, then divide by 2."
        explanation = "First, subtract 3 from both sides."
        result = await agent.run(question, answer, explanation, thread_id="thread-001")
        print("\nFinal explanation:\n", result["improved_explanation"])

    asyncio.run(test())
