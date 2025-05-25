import asyncio
from uuid import uuid4

import httpx
from a2a.client import A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

async def ask_reasoning(question: str, thread_id: str):
    async with httpx.AsyncClient() as httpx_client:
        client = await A2AClient.get_client_from_agent_card_url(httpx_client, "http://localhost:9002")
        # Build a user message
        msg = {
            "role": "user",
            "messageId": uuid4().hex,
            "parts": [{"type":"text", "text": question}],
        }
        params = MessageSendParams(message=msg)
        req = SendMessageRequest(params=params)
        resp = await client.send_message(req)
        # Extract what the Reasoning Agent returned:
        data = resp.result
        # It should contain the simplified_explanation field
        text = data["parts"][0]["text"]
        return text

async def ask_teaching(question, answer, explanation, feedback_history, thread_id):
    async with httpx.AsyncClient() as httpx_client:
        client = await A2AClient.get_client_from_agent_card_url(httpx_client, "http://localhost:9001")
        # We’ll send a “fake user” message where the input is a dict, so we need to
        # hack the A2AClient a bit, because by default it expects BaseMessage
        payload = {
            "skill_id": "simplify_explanation",
            "input": {
                "question": question,
                "answer": answer,
                "explanation": explanation,
                "feedback_history": feedback_history,
                "thread_id": thread_id
            }
        }
        # Bypass A2AClient and call /tasks directly
        r = await httpx_client.post("http://localhost:9001/tasks", json=payload, timeout=30.0)
        r.raise_for_status()
        out = r.json()["output"]
        return out["improved_explanation"], out.get("feedback_history", feedback_history)

async def main():
    thread = "test-thread-001"
    question = "Solve 2x + 3 = 7"
    print(f"User  {question}")

    # Step 1: Reasoning Agent solves + simplifies
    simp = await ask_reasoning(question, thread)
    print(f" Assistant  {simp}")

    # Step 2: User gives feedback
    feedback = input(" User feedback (e.g. 'I dont get why you subtracted 3'): ")

    # Step 3: Call Teaching Agent directly with history
    #   We need the raw answer & raw explanation too —
    #   for now, split simp to extract answer/explanation or store them in ask_reasoning
    #   But assuming simp = "Answer: x=2  Explanation: ...", we can parse:
    parts = simp.split("Explanation:")
    answer_part = parts[0].replace("Answer:", "").strip()
    explanation_part = parts[1].strip() if len(parts) > 1 else ""
    improved, history = await ask_teaching(
        question, answer_part, explanation_part, [feedback], thread
    )
    print(f" Refined {improved}")

if __name__ == "__main__":
    asyncio.run(main())
