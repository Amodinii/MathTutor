import asyncio
import httpx
import os
import json
import ast
from uuid import uuid4
from datetime import datetime

from a2a.client.client import A2AClient
from a2a.types import MessageSendParams, SendMessageRequest

from Tutor.Logging.Logger import logger  # Adjust this import based on your project layout

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
    response_data = response.model_dump(mode="json", exclude_none=True)

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
        print(f"[A2A Client Scraping] Total questions extracted: {len(extracted)}")
    else:
        logger.warning("[A2A Client Scraping] No questions extracted from artifacts.")


async def main():
    timeout = httpx.Timeout(
        connect=30.0,
        read=300.0,
        write=30.0,
        pool=30.0
    )

    async with httpx.AsyncClient(timeout=timeout) as httpx_client:
        try:
            # Connect to scraping agent
            client = await A2AClient.get_client_from_agent_card_url(
                httpx_client, "http://localhost:10000"
            )
        except Exception as e:
            logger.error(f"[A2A Client Scraping] Failed to connect to agent: {e}")
            return

        # Define input payload
        payload = {
            "message": {
                "role": "user",
                "parts": [
                    {
                        "type": "text",
                        "text": (
                            "{'query': 'If ABCD is a quadrilateral with AB = 3, BC = 4, CD = 5, and DA = 6, what is the area of ABCD?',"
                            "'follow_up_questions': None,"
                            "'answer': None,"
                            "'images': [],"
                            "'results': ["
                            "{'title': 'Find the area of a quadrilateral ABCD in which AB = 3 cm, BC = 4 cm, CD ...',"
                            "'url': 'https://www.cuemath.com/ncert-solutions/find-the-area-of-a-quadrilateral-abcd-in-which-ab-3-cm-bc-4-cm-cd-4-cm-da-5-cm-and-ac-5-cm/',"
                            "'content': 'AB 2 + BC 2 = 3 2 + 4 2 = 25 = 5 2. ⇒ 5 2 = AC 2. Since ∆ABC obeys the Pythagoras theorem, we can say ∆ABC is right-angled at B. Therefore, the area of ΔABC = 1/2 × base × height = 1/2 × 3 cm × 4 cm = 6 cm 2. Area of ΔABC = 6 cm 2. Now, In ∆ADC. we have a = 5 cm, b = 4 cm and c = 5 cm. Semi Perimeter: s = Perimeter/2. s = (a + b',"
                            "'score': 0.8745175,"
                            "'raw_content': None}"
                            "],"
                            "'response_time': 2.16}"
                        ),
                    }
                ],
                "messageId": uuid4().hex,
            }
        }

        request = SendMessageRequest(params=MessageSendParams(**payload))

        logger.info("[A2A Client Scraping] Sending request to scraping agent...")
        logger.info("[A2A Client Scraping] This may take 2-3 minutes for web scraping and LLM processing...")

        try:
            response = await client.send_message(request)
            save_response_artifacts(response)
        except Exception as e:
            logger.error(f"[A2A Client Scraping] Error occurred while sending request: {e}")


if __name__ == "__main__":
    asyncio.run(main())
