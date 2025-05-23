from Tutor.Agents.Reasoning import build_reasoning_agent

agent = build_reasoning_agent()
response = agent("What is the derivative of x^2 * sin(x)?")

print(response["result"])
