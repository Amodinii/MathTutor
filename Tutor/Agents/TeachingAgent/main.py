import sys
import json
import os
import asyncio
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException
from .Teaching import run_teaching

app = FastAPI()

# Agent Card endpoint
@app.get("/.well-known/agent.json")
def agent_card():
    path = os.path.join(os.path.dirname(__file__), "agent_card.yaml")
    import yaml
    with open(path) as f:
        card = yaml.safe_load(f)
    return JSONResponse(content=card)

# Tasks endpoint
@app.post("/tasks")
async def tasks(request: Request):
    try:
        task = await request.json()
        skill = task.get("skill_id")
        inp = task.get("input", {})
        if skill != "simplify_explanation":
            raise HTTPException(400, f"Unknown skill_id: {skill}")

        result_state = await run_teaching(inp)
        return {
            "status": "completed",
            "output": {
                "improved_explanation": result_state["improved_explanation"],
                "feedback_history": result_state["feedback_history"]
            }
        }
    except TutorException as te:
        logger.error(f"[TeachingAgent] TutorException: {te}")
        raise HTTPException(500, str(te))
    except Exception as e:
        logger.error(f"[TeachingAgent] unexpected error: {e}")
        raise HTTPException(500, str(e))
