import asyncio
import httpx
import os
import json
from uuid import uuid4
from datetime import datetime

from a2a.client.client import A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

from Tutor.Logging.Logger import logger 
AGENT_BASE_URL = "http://localhost:9001" 


import os
from datetime import datetime
from Tutor.Logging.Logger import logger

def save_response_artifacts(response_text: str):
    final_dir = "Tutor/Agents/TeachingAgent/response"
    os.makedirs(final_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    final_txt_filename = f"simplified_explanation_{timestamp}.txt"
    final_txt_path = os.path.join(final_dir, final_txt_filename)

    try:
        with open(final_txt_path, "w", encoding="utf-8") as f_txt:
            f_txt.write(response_text.strip())
        logger.info(f"[A2A Client Teaching] Simplified explanation saved as TXT: {final_txt_path}")
        print(f"[A2A Client Teaching] Simplified Explanation:\n{response_text}")
    except Exception as e:
        logger.exception(f"[A2A Client Teaching] Failed to save explanation: {e}")


async def main():
    timeout = httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0)

    # User input to simplify
    input_payload = {
        "question": "If a rectangle has a length of 8 cm and a width of 3 cm, what is its area?",
        "answer": "24",
        "explanation": "The area of a rectangle is found by multiplying the length by the width, so 8 * 3 = 24.",
        "feedback_history": [],
        "thread_id": "test-thread-001"
    }

    # Format as stringified JSON to send in a text part
    input_text = json.dumps(input_payload)

    payload = {
        "message": {
            "role": "user",
            "parts": [
                {
                    "type": "text",
                    "text": input_text
                }
            ],
            "messageId": uuid4().hex
        }
    }

    try:
        async with httpx.AsyncClient(timeout=timeout) as httpx_client:
            logger.info("[A2A Client Teaching] Connecting to agent...")
            client = await A2AClient.get_client_from_agent_card_url(httpx_client, AGENT_BASE_URL)

            request = SendMessageRequest(params=MessageSendParams(**payload))

            logger.info("[A2A Client Teaching] Sending message to teaching agent...")
            response = await client.send_message(request)
            response = response.root.result.artifacts[0].parts[0].root.text
            print("Obtained response")
            print(response)
            print(type(response))
            print("Saving")
            save_response_artifacts(response)
            print("Saved")

    except Exception as e:
        logger.error(f"[A2A Client Teaching] Error during request: {e}")
        print(f"ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(main())