from typing import TypedDict, Literal
from langgraph.a2a import agent, create_dispatcher, AgentContext
from Tutor.Services.TeachingModel import TeachingModel
from Schemas.teaching_context import TeachingContext

# --- Define lightweight message schema ---
class Message(TypedDict):
    question: str
    answer: str
    explanation: str
    source: Literal["web", "user"]
    user_feedback: str


# --- Initialize Teaching Model ---
teaching_model = TeachingModel(model_name="mixtral-8x7b-32768")


# --- Reasoning Agent ---
@agent
async def reasoning_agent(ctx: AgentContext[Message]):
    print("[reasoning_agent] solving question...")
    msg = ctx.message.copy()
    msg["answer"] = "x = 2"
    msg["explanation"] = "Subtract 3 from both sides, then divide by 2."
    yield ctx.send("teaching_agent", msg)


# --- Teaching Agent (MCP-powered) ---
@agent(schema=TeachingContext)
async def teaching_agent(ctx: AgentContext[TeachingContext]):
    memory = ctx.context
    print("[teaching_agent] simplifying explanation with context...")

    memory.explanation = teaching_model.teach(
        question=memory.question,
        answer=memory.answer,
        explanation=memory.explanation,
        feedback_history=memory.student_feedback_history
    )

    yield ctx.send("human_review", {
        "question": memory.question,
        "answer": memory.answer,
        "explanation": memory.explanation,
        "source": ctx.message["source"]
    })


# --- Human Review Agent ---
@agent
async def human_review(ctx: AgentContext[Message]):
    msg = ctx.message.copy()
    print("\n🤖 Explanation:", msg["explanation"])
    feedback = input("👤 What do you think? (type anything): ").strip()
    msg["user_feedback"] = feedback
    yield ctx.send("controller", msg)


# --- Controller (MCP-powered) ---
@agent(schema=TeachingContext)
async def controller(ctx: AgentContext[TeachingContext]):
    msg = ctx.message
    memory = ctx.context
    feedback = msg["user_feedback"]
    memory.student_feedback_history.append(feedback)

    print(f"[controller] feedback = {feedback}")

    if "wrong" in feedback.lower():
        yield ctx.send("reasoning_agent", msg)
    elif "understand" in feedback.lower() and "not" not in feedback.lower():
        if msg["source"] == "web":
            yield ctx.send("forward_agent", msg)
        else:
            print("[controller] done (source=user).")
    else:
        yield ctx.send("teaching_agent", msg)


# --- Forward Agent ---
@agent
async def forward_agent(ctx: AgentContext[Message]):
    msg = ctx.message
    print(f"[forward_agent] forwarding to web system: {msg['question']} -> {msg['answer']}")
    return  # End


# --- Dispatcher ---
def build_graph():
    return create_dispatcher({
        "reasoning_agent": reasoning_agent,
        "teaching_agent": teaching_agent,
        "human_review": human_review,
        "controller": controller,
        "forward_agent": forward_agent,
    })
