import asyncio
from Tutor.Agents.ReasoningAgent.Reasoning import build_reasoning_agent
from Tutor.Agents.Scrape import build_scraping_agent
from Tutor.Logging.Logger import logger

async def main():
    # run_agent = await build_reasoning_agent()
    # result = await run_agent("Let angle A be 150 degrees. Calculate all the three equal angles of the quadrilateral.")
    # print("Agent response:\n", result)
    # await run_agent.cleanup()

    fake_scraped_data = {'query': 'If ABCD is a quadrilateral with AB = 3, BC = 4, CD = 5, and DA = 6, what is the area of ABCD?',
    'follow_up_questions': None,
    'answer': None,
    'images': [],
    'results': [
    {'title': 'Question 2 - Find area of a quadrilateral ABCD in which - Teachoo',
    'url': 'https://www.teachoo.com/1295/464/Ex-12.2--2---Find-area-of-a-quadrilateral-ABCD-in-which/category/Ex-12.2/',
    'content': 'Transcript. Question 2 Find the area of a quadrilateral ABCD in which AB = 3 cm, BC = 4 cm, CD = 4 cm, DA = 5 cm and AC = 5 cm. Area of Quadrilateral = Area of ΔABC',
    'score': 0.8430832,
    'raw_content': None},
    # {'title': 'Find the area of a quadrilateral ABCD in which AB = 3 cm, BC = 4 cm, CD ...',
    # 'url': 'https://www.cuemath.com/ncert-solutions/find-the-area-of-a-quadrilateral-abcd-in-which-ab-3-cm-bc-4-cm-cd-4-cm-da-5-cm-and-ac-5-cm/',
    # 'content': 'AB 2 + BC 2 = 3 2 + 4 2 = 25 = 5 2. ⇒ 5 2 = AC 2. Since ∆ABC obeys the Pythagoras theorem, we can say ∆ABC is right-angled at B. Therefore, the area of ΔABC = 1/2 × base × height = 1/2 × 3 cm × 4 cm = 6 cm 2. Area of ΔABC = 6 cm 2. Now, In ∆ADC. we have a = 5 cm, b = 4 cm and c = 5 cm. Semi Perimeter: s = Perimeter/2. s = (a + b',
    # 'score': 0.8745175,
    # 'raw_content': None}
    ],
    'response_time': 2.16}

    scraping_agent = await build_scraping_agent()
    result = await scraping_agent(fake_scraped_data)
    logger.info(f"Obtained Result : \n {result}")

if __name__ == "__main__":
    asyncio.run(main())