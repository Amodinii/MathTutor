import sys
from langgraph.graph import StateGraph, END
from Tutor.MCPClients.VectorDB import VectorDBClient
from Tutor.MCPClients.WebSearch import WebSearchClient
from Tutor.Services.ReasoningModel import ReasoningModel
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

# Define state
class AgentState(dict):
    pass

# Define node: Retrieve from VectorDB
def retrieve_from_vector_db(state: AgentState) -> AgentState:
    question = state["question"]
    try:
        vector_client = state["vector_client"]
        docs = vector_client.retrieve_documents(query=question)
        logger.info(f"[Reasoning Agent] Retrieved {len(docs)} docs from Vector DB.")
        state["documents"] = docs
        return state
    except Exception as e:
        raise TutorException(e, sys)

# Define router
def router(state: AgentState) -> str:
    docs = state.get("documents", [])
    if docs:
        logger.info("[Reasoning Agent] Routing to Reasoning step.")
        return "reason"
    else:
        logger.info("[Reasoning Agent] Routing to Web Search as fallback.")
        return "web_search"

# Define node: Fallback to Web Search
def retrieve_from_web(state: AgentState) -> AgentState:
    question = state["question"]
    try:
        web_client = state["web_client"]
        search_results = web_client.search(question)
        logger.info(f"[Reasoning Agent] Retrieved fallback results from Web Search.")
        state["documents"] = search_results
        return state
    except Exception as e:
        raise TutorException(e, sys)

# Define node: Reasoning
def reasoning_node(state: AgentState) -> AgentState:
    try:
        model = state["reasoning_model"]
        question = state["question"]
        documents = state["documents"]
        result = model.reason(question=question)
        logger.info("[Reasoning Agent] Completed reasoning.")
        state["result"] = result
        return state
    except Exception as e:
        raise TutorException(e, sys)

# Construct the Reasoning Agent
def build_reasoning_agent(model_name="llama3-8b-8192", vector_url="http://localhost:5000", web_url="http://localhost:6000"):
    try:
        vector_client = VectorDBClient(server_url=vector_url)
        web_client = WebSearchClient(server_url=web_url)
        reasoning_model = ReasoningModel(model_name=model_name, vector_db=vector_client)

        workflow = StateGraph(AgentState)
        workflow.add_node("vector_db", retrieve_from_vector_db)
        workflow.add_node("web_search", retrieve_from_web)
        workflow.add_node("reason", reasoning_node)

        workflow.set_entry_point("vector_db")
        workflow.add_conditional_edges("vector_db", router, {
            "web_search": "web_search",
            "reason": "reason"
        })
        workflow.add_edge("web_search", "reason")
        workflow.add_edge("reason", END)

        app = workflow.compile()

        def run_agent(question: str):
            state = AgentState({
                "question": question,
                "vector_client": vector_client,
                "web_client": web_client,
                "reasoning_model": reasoning_model
            })
            return app.invoke(state)

        return run_agent

    except Exception as e:
        raise TutorException(e, sys)