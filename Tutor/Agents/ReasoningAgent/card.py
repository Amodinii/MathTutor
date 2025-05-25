from a2a.types import AgentCard, AgentSkill, AgentCapabilities

solve_skill = AgentSkill(
    id="solve_and_explain",
    name="Solve and Explain",
    description="Solves a math question and delegates explanation simplification.",
    tags=["math", "reasoning", "explanation"],
    examples=[
        "x+2=5",
        "How do I find the derivative of x^2?"
    ],
)

agent_card = AgentCard(
    name="Reasoning Agent",
    description="Retrieves context, reasons, and calls a Teaching Agent to simplify.",
    url="http://localhost:9002",
    version="1.0.0",
    defaultInputModes=["text"],
    defaultOutputModes=["text"],
    capabilities=AgentCapabilities(streaming=False),
    skills=[solve_skill],
)
