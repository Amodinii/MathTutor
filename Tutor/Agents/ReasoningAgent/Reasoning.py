import sys
import os
from datetime import datetime
import ast
import json
import httpx
from uuid import uuid4
from typing import TypedDict, List, Any, Optional
from langgraph.graph import StateGraph, END
from Tutor.MCPClients.VectorDB import VectorDBClient
from Tutor.MCPClients.WebSearch import WebSearchClient
from Tutor.Services.ReasoningModel import ReasoningModel
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

def save_response_artifacts(response):
    # Create folders
    raw_dir = "Tutor/Agents/ScrapingAgent/response/raw"
    final_dir = "Tutor/Agents/ScrapingAgent/response/final"
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(final_dir, exist_ok=True)

    # Timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_filename = f"scraping_response_raw_{timestamp}.json"
    final_filename = f"scraped_questions_{timestamp}.json"

    # Convert full response to JSON
    response_data = response if isinstance(response, dict) else response.model_dump(mode="json", exclude_none=True)

    # Save full raw response
    raw_path = os.path.join(raw_dir, raw_filename)
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(response_data, f, indent=2, ensure_ascii=False)
    logger.info(f"[A2A Client Scraping] Raw response saved: {raw_path}")

    # Try to extract artifact with questions
    artifacts = response_data.get("result", {}).get("artifacts", [])
    extracted = []

    for artifact in artifacts:
        if artifact.get("name") == "scraped_questions":
            for part in artifact.get("parts", []):
                if part.get("kind") == "text":
                    raw_text = part.get("text", "")
                    try:
                        questions = json.loads(raw_text)
                    except json.JSONDecodeError:
                        try:
                            questions = ast.literal_eval(raw_text)
                        except Exception as e:
                            logger.warning(f"[A2A Client Scraping] Failed to parse text as JSON or Python literal: {e}")
                            questions = None

                    if isinstance(questions, list):
                        extracted.extend(questions)
                    elif isinstance(questions, dict):
                        extracted.append(questions)

    if extracted:
        final_path = os.path.join(final_dir, final_filename)
        with open(final_path, "w", encoding="utf-8") as f:
            json.dump(extracted, f, indent=2, ensure_ascii=False)
        logger.info(f"[A2A Client Scraping] Extracted questions saved: {final_path}")
        logger.info(f"[A2A Client Scraping] Total questions extracted: {len(extracted)}")
    else:
        logger.warning("[A2A Client Scraping] No questions extracted from artifacts.")

# Define state with proper typing
class AgentState(TypedDict):
    question: str
    vector_client: Optional[Any]
    web_client: Optional[Any]
    reasoning_model: Optional[Any]
    documents: Optional[List[Any]]
    has_documents: Optional[bool]
    result: Optional[Any]

# Async node: Retrieve from VectorDB
async def retrieve_from_vector_db(state: AgentState) -> AgentState:
    question = state.get("question")
    if not question:
        logger.error("[Reasoning Agent] No question provided to vector DB retrieval")
        state["documents"] = []
        state["has_documents"] = False
        return state
        
    try:
        vector_client = state.get("vector_client")
        if not vector_client:
            logger.error("[Reasoning Agent] No vector client available")
            state["documents"] = []
            state["has_documents"] = False
            return state
            
        docs = await vector_client.retrieve_documents(query=question)
        logger.info(f"[Reasoning Agent] Retrieved {len(docs)} docs from Vector DB.")
        state["documents"] = docs
        state["has_documents"] = len(docs) > 0
        return state
    except Exception as e:
        logger.error(f"[Reasoning Agent] Error retrieving from vector DB: {e}")
        state["documents"] = []
        state["has_documents"] = False
        return state

# Router node (sync, because it's just logic on state)
def router(state: AgentState) -> str:
    has_docs = state.get("has_documents", False)
    if has_docs:
        logger.info("[Reasoning Agent] Routing to Reasoning step with Vector DB docs.")
        return "reason"
    else:
        logger.info("[Reasoning Agent] Routing to Web Search as fallback.")
        return "web_search"

# Async node: Fallback to Web Search
async def retrieve_from_web(state: AgentState) -> AgentState:
    question = state.get("question")
    if not question:
        logger.error("[Reasoning Agent] No question provided to web search")
        raise TutorException("No question provided to web search", sys)
        
    try:
        web_client = state.get("web_client")
        if not web_client:
            logger.error("[Reasoning Agent] No web client available")
            raise TutorException("No web client available", sys)
            
        search_results = await web_client.search(query=question)
        result = json.loads(search_results.content[0].text)
        logger.info(f"[Reasoning Agent] Retrieved fallback results from Web Search.")
        SCRAPING_AGENT_URL = "http://localhost:10000"
        SCRAPING_SKILL_ID = "extract_questions"
        logger.info("[Reasoning Agent] Connecting to scraping agent.")
        logger.info(f"[Reasoning Agent] Scraping agent URL: {SCRAPING_AGENT_URL} and skill ID: {SCRAPING_SKILL_ID}")

        payload = {
            "params": {
                "skill": SCRAPING_SKILL_ID,
                "message": {
                    "role": "user",
                    "parts": [
                        {
                            "type": "text",
                            "text": str(result),
                        }
                    ],
                    "messageId": uuid4().hex,
                }
            }
        }


        try:
            timeout = httpx.Timeout(
                connect=30.0,
                read=300.0,
                write=30.0,
                pool=30.0
            )
            async with httpx.AsyncClient(timeout=timeout) as client:
                logger.info("[Reasoning Agent] Requesting scraping agent.")
                response = await client.post(
                    SCRAPING_AGENT_URL,
                    json={"skill": SCRAPING_SKILL_ID, **payload},
                )
                result_data = response.json()
                save_response_artifacts(result_data)
        except Exception as te:
                logger.warning(f"[ReasoningAgentExecutor] Scraping Agent call failed: {te}")

        state["documents"] = result
        state["has_documents"] = True
        return state
    except Exception as e:
        logger.error(f"[Reasoning Agent] Error retrieving from web search: {e}")
        raise TutorException(e, sys)

# Async node: Reasoning
async def reasoning_node(state: AgentState) -> AgentState:
    try:
        model = state.get("reasoning_model")
        question = state.get("question")
        documents = state.get("documents", [])
        
        if not model:
            logger.error("[Reasoning Agent] No reasoning model available")
            raise TutorException("No reasoning model available", sys)
            
        if not question:
            logger.error("[Reasoning Agent] No question provided to reasoning")
            raise TutorException("No question provided to reasoning", sys)
        
        # Pass both question and retrieved documents to reasoning model
        result = await model.reason(question=question, documents=documents)
        logger.info("[Reasoning Agent] Completed reasoning.")
        state["result"] = result
        return state
    except Exception as e:
        logger.error(f"[Reasoning Agent] Error in reasoning: {e}")
        raise TutorException(e, sys)

class ReasoningAgent:
    def __init__(self, model_name="llama3-8b-8192"):
        self.model_name = model_name
        self.vector_client = None
        self.web_client = None
        self.reasoning_model = None
        self.app = None

    async def initialize(self):
        """Initialize and connect all components"""
        try:
            # Initialize async MCP clients
            self.vector_client = VectorDBClient()
            self.web_client = WebSearchClient()

            await self.vector_client.connect()
            await self.web_client.connect()

            # Initialize reasoning model (without passing vector_client to avoid duplication)
            self.reasoning_model = ReasoningModel(model_name=self.model_name)

            # Build LangGraph workflow
            workflow = StateGraph(AgentState)
            workflow.add_node("vector_db", retrieve_from_vector_db)
            workflow.add_node("web_search", retrieve_from_web)
            workflow.add_node("reason", reasoning_node)

            workflow.set_entry_point("vector_db")
            workflow.add_conditional_edges("vector_db", router, {
                "reason": "reason",
                "web_search": "web_search"
            })
            workflow.add_edge("web_search", "reason")
            workflow.add_edge("reason", END)

            self.app = workflow.compile()
            logger.info("[Reasoning Agent] Successfully initialized.")

        except Exception as e:
            await self.cleanup()
            raise TutorException(e, sys)

    async def run(self, question: str):
        """Run the reasoning agent on a question"""
        if not self.app:
            raise TutorException("Agent not initialized. Call initialize() first.", sys)
        
        if not question or not question.strip():
            raise TutorException("Question cannot be empty", sys)
        
        try:
            # Create initial state with proper structure
            initial_state = AgentState(
                question=question.strip(),
                vector_client=self.vector_client,
                web_client=self.web_client,
                reasoning_model=self.reasoning_model,
                documents=None,
                has_documents=None,
                result=None
            )
            
            logger.info(f"[Reasoning Agent] Starting with question: {question[:100]}...")
            result = await self.app.ainvoke(initial_state)
            return result.get("result")
            
        except Exception as e:
            logger.error(f"[Reasoning Agent] Error running agent: {e}")
            raise TutorException(e, sys)

    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.vector_client:
                await self.vector_client.close()
            if self.web_client:
                await self.web_client.close()
            logger.info("[Reasoning Agent] Cleaned up resources.")
        except Exception as e:
            logger.error(f"[Reasoning Agent] Error during cleanup: {e}")

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.cleanup()

# Convenience function for backward compatibility
async def build_reasoning_agent(model_name="llama3-8b-8192"):
    """
    Build and return a reasoning agent runner function.
    Note: Remember to properly clean up resources when done.
    """
    try:
        agent = ReasoningAgent(model_name)
        await agent.initialize()
        
        async def run_agent(question: str):
            return await agent.run(question)
        
        # Attach cleanup method to the runner for manual cleanup
        run_agent.cleanup = agent.cleanup
        
        return run_agent

    except Exception as e:
        raise TutorException(e, sys)