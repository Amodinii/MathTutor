import asyncio
from Tutor.Agents.Reasoning import build_reasoning_agent

async def main():
    run_agent = await build_reasoning_agent()
    result = await run_agent("Let angle A be 150 degrees. Calculate all the three equal angles of the quadrilateral.")
    print("Agent response:\n", result)
    await run_agent.cleanup()  # Don't forget this part!

if __name__ == "__main__":
    asyncio.run(main())