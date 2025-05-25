import sys
import os
import yaml
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx

from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException
from .Reasoning import run_reasoning

app = FastAPI()

# URL of the Teaching Agent’s /tasks endpoint
TEACHING_AGENT_URL = "http://localhost:9001/tasks"

# ——— Agent Card Endpoint ———
@app.get("/.well-known/agent.json")
def agent_card():
    path = os.path.join(os.path.dirname(__file__), "agent_card.yaml")
    with open(path) as f:
        card = yaml.safe_load(f)
    return JSONResponse(content=card)

@app.get("/describe")
def describe():
    path = os.path.join(os.path.dirname(__file__), "agent_card.yaml")
    with open(path) as f:
        card = yaml.safe_load(f)
    return JSONResponse(content=card)

# ——— Tasks Endpoint ———
@app.post("/tasks")
async def tasks(request: Request):
    """
    Expects JSON:
    {
      "skill_id": "solve_and_explain",
      "input": {
        "question": "...",
        "thread_id": "optional-session-id"
      }
    }
    """
    try:
        task = await request.json()
        skill = task.get("skill_id")
        inp = task.get("input", {})

        if skill != "solve_and_explain":
            raise HTTPException(400, f"Unknown skill_id: {skill}")

        # 1) Run the LangGraph reasoning workflow
        reasoning_output = await run_reasoning(inp)
        answer = reasoning_output.get("answer", "")
        explanation = reasoning_output.get("explanation", "")

        # 2) Delegate to Teaching Agent for simplification
        teach_payload = {
            "skill_id": "simplify_explanation",
            "input": {
                "question": inp["question"],
                "answer": answer,
                "explanation": explanation,
                "feedback_history": [],
                "thread_id": inp.get("thread_id")
            }
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(TEACHING_AGENT_URL, json=teach_payload)
            resp.raise_for_status()
            teach_out = resp.json().get("output", {})

        simplified = teach_out.get("improved_explanation") or teach_out.get("simplified_explanation")

        return {
            "status": "completed",
            "output": {
                "answer": answer,
                "simplified_explanation": simplified
            }
        }

    except TutorException as te:
        logger.error(f"[ReasoningAgent] TutorException: {te}")
        raise HTTPException(500, str(te))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[ReasoningAgent] unexpected error: {e}")
        raise HTTPException(500, str(e))
