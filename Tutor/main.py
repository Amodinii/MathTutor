import asyncio
from Tutor.Agents.Reasoning import ReasoningAgent

async def main():
    async with ReasoningAgent("llama3-8b-8192") as agent:
        response = await agent.run("What is the derivative of x^2 * sin(x)?")
        print(response)

if __name__ == "__main__":
    asyncio.run(main())