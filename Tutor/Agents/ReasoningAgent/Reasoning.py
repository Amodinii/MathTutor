import sys
import ast
import asyncio
from typing import TypedDict, List, Any, Optional
from langgraph.graph import StateGraph, END

from Tutor.MCPClients.VectorDB import VectorDBClient
from Tutor.MCPClients.WebSearch import WebSearchClient
from Tutor.Services.ReasoningModel import ReasoningModel
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

# ——— State Schema ———
class AgentState(TypedDict):
    question: str
    vector_client: Optional[Any]
    web_client: Optional[Any]
    reasoning_model: Optional[Any]
    documents: Optional[List[Any]]
    has_documents: Optional[bool]
    result: Optional[dict]
    thread_id: Optional[str]

# ——— Nodes ———
async def retrieve_from_vector_db(state: AgentState) -> AgentState:
    q = state["question"]
    logger.debug(f"[Node: VectorDB] Starting retrieval for question: {q}")
    if not q:
        logger.warning("[Node: VectorDB] Question is empty. Skipping retrieval.")
        state.update(documents=[], has_documents=False)
        return state

    try:
        vc = state["vector_client"]
        docs = await vc.retrieve_documents(query=q) if vc else []
        logger.info(f"[Node: VectorDB] Retrieved {len(docs)} document(s).")
        state.update(documents=docs, has_documents=bool(docs))
    except Exception as e:
        logger.error(f"[Node: VectorDB] Retrieval error: {e}")
        state.update(documents=[], has_documents=False)
    return state

def router(state: AgentState) -> str:
    route = "reason" if state.get("has_documents") else "web_search"
    logger.debug(f"[Router] Routing to: {route}")
    return route

async def retrieve_from_web(state: AgentState) -> AgentState:
    q = state["question"]
    logger.debug(f"[Node: WebSearch] Searching for question: {q}")
    try:
        wc = state["web_client"]
        results = await wc.search(query=q) if wc else []
        logger.info(f"[Node: WebSearch] Retrieved {len(results)} result(s).")
        state.update(documents=results, has_documents=bool(results))
    except Exception as e:
        logger.error(f"[Node: WebSearch] Search error: {e}")
        state.update(documents=[], has_documents=False)
    return state

async def reasoning_node(state: AgentState) -> AgentState:
    try:
        q = state["question"]
        docs = state.get("documents", [])
        logger.debug(f"[Node: Reasoning] Starting reasoning on question: {q}")
        logger.debug(f"[Node: Reasoning] Using {len(docs)} document(s) for context.")
        model = state["reasoning_model"]
        result = await model.reason(question=q, documents=docs)
        result = result
        logger.info(f"[Node: Reasoning] Reasoning completed. Answer: {result}")
        state["result"] = result
    except Exception as e:
        logger.error(f"[Node: Reasoning] Reasoning error: {e}")
        raise TutorException(e, sys)
    return state

# ——— Build & compile the graph ———
graph = StateGraph(AgentState)
graph.add_node("vector_db", retrieve_from_vector_db)
graph.add_node("web_search", retrieve_from_web)
graph.add_node("reason", reasoning_node)

graph.set_entry_point("vector_db")
graph.add_conditional_edges("vector_db", router, {
    "reason": "reason",
    "web_search": "web_search"
})
graph.add_edge("web_search", "reason")
graph.add_edge("reason", END)

runnable = graph.compile()

# ——— Public API ———
async def run_reasoning(input_data: dict) -> dict:
    """
    input_data: { question: str, thread_id?: str }
    returns: { answer: str, explanation: str }
    """
    try:
        logger.debug(f"[ReasoningAgent] run_reasoning called with input: {input_data}")
        state: AgentState = {
            "question": input_data["question"],
            "vector_client": VectorDBClient(),    # or reuse a shared instance
            "web_client": WebSearchClient(),
            "reasoning_model": ReasoningModel(model_name="llama3-8b-8192"),
            "documents": None,
            "has_documents": None,
            "result": None,
            "thread_id": input_data.get("thread_id")
        }

        logger.debug("[ReasoningAgent] Starting LangGraph execution.")
        final_state = await runnable.ainvoke(state)
        logger.debug(f"[ReasoningAgent] Final state: {final_state}")
        return final_state["result"] or {}
    except Exception as e:
        logger.error(f"[ReasoningAgent] Failed in run_reasoning: {e}")
        raise TutorException(e, sys)