import asyncio
import httpx
import os
import json
import ast
from uuid import uuid4
from datetime import datetime

from a2a.client.client import A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

from Tutor.Logging.Logger import logger


def save_response_artifacts(response):
    raw_dir = "Tutor/Agents/ReasoningAgent/response/raw"
    final_dir = "Tutor/Agents/ReasoningAgent/response/final"
    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(final_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    raw_filename = f"reasoning_response_raw_{timestamp}.json"
    final_filename = f"reasoning_result_{timestamp}.json"

    response_data = response.model_dump(mode="json", exclude_none=True)

    raw_path = os.path.join(raw_dir, raw_filename)
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(response_data, f, indent=2, ensure_ascii=False)
    logger.info(f"[A2A Client Reasoning] Raw response saved: {raw_path}")

    artifacts = response_data.get("result", {}).get("artifacts", [])
    extracted = []

    for artifact in artifacts:
        if artifact.get("name") == "reasoning_result":
            for part in artifact.get("parts", []):
                if part.get("kind") == "text":
                    raw_text = part.get("text", "")
                    try:
                        data = json.loads(raw_text)
                    except json.JSONDecodeError:
                        try:
                            data = ast.literal_eval(raw_text)
                        except Exception as e:
                            logger.warning(f"[A2A Client Reasoning] Failed to parse text: {e}")
                            data = None

                    if isinstance(data, list):
                        extracted.extend(data)
                    elif isinstance(data, dict):
                        extracted.append(data)

    if extracted:
        final_path = os.path.join(final_dir, final_filename)
        with open(final_path, "w", encoding="utf-8") as f:
            json.dump(extracted, f, indent=2, ensure_ascii=False)
        logger.info(f"[A2A Client Reasoning] Extracted reasoning result saved: {final_path}")
        print(f"[A2A Client Reasoning] Total items extracted: {len(extracted)}")
    else:
        logger.warning("[A2A Client Reasoning] No result extracted from artifacts.")


async def main():
    timeout = httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=30.0)

    async with httpx.AsyncClient(timeout=timeout) as httpx_client:
        try:
            client = await A2AClient.get_client_from_agent_card_url(
                httpx_client, "http://localhost:9002"
            )
        except Exception as e:
            logger.error(f"[A2A Client Reasoning] Failed to connect to agent: {e}")
            return

        question_payload = {
            "question": "If a rectangle has a length of 8 cm and a width of 3 cm, what is its area?",
            "thread_id": "test-thread-001"
        }

        message_payload = {
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": str(question_payload)
                    }
                ],
                "messageId": uuid4().hex,
            }
        }

        request = SendMessageRequest(params=MessageSendParams(**message_payload))

        logger.info("[A2A Client Reasoning] Sending request to Reasoning Agent...")
        logger.info("[A2A Client Reasoning] This may take 1 - 2 minutes due to reasoning and explanation simplification...")

        try:
            response = await client.send_message(request)
            save_response_artifacts(response)
        except Exception as e:
            logger.error(f"[A2A Client Reasoning] Error occurred while sending request: {e}")


if __name__ == "__main__":
    asyncio.run(main())