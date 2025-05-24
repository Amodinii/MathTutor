from typing import List, Optional
from langgraph.mcp import mcp_schema

@mcp_schema
class TeachingContext:
    question: str
    answer: str
    explanation: Optional[str] = None
    student_feedback_history: List[str] = []