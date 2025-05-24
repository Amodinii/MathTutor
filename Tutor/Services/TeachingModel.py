import sys
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

from langchain_groq import ChatGroq
from langchain.prompts.chat import ChatPromptTemplate
import asyncio

class TeachingModel:
    def __init__(self, model_name):
        try:
            self.llm = ChatGroq(
                model=model_name,
                temperature=0.7,
                max_retries=2
            )

            system_message = """
You are a helpful math tutor. You are explaining a math solution step-by-step.
The user may ask follow-up questions or express confusion.

If this is the first time, explain the solution simply.
If the user has provided feedback or follow-ups, refine or expand your explanation.
"""

            human_message = """
Question: {question}
Answer: {answer}
Current Explanation: {explanation}
Feedback History:
{feedback_history}
"""

            self.prompt = ChatPromptTemplate.from_messages([
                ("system", system_message),
                ("human", human_message)
            ])

            logger.info(f"Teaching model {model_name} initialized successfully with Groq.")
        except Exception as e:
            logger.error("Error initializing teaching model.")
            raise TutorException(e, sys)

    def teach(self, question, answer, explanation=None, feedback_history=None, thread_id=None):
        try:
            logger.info(f"Teaching session started for thread: {thread_id}")
            feedback_text = "\n".join(feedback_history or [])
            chain = self.prompt | self.llm
            model_response = chain.invoke({
                "question": question,
                "answer": answer,
                "explanation": explanation or "",
                "feedback_history": feedback_text
            })
            return model_response.content.strip()
        except Exception as e:
            logger.error("Error teaching student.")
            raise TutorException(e, sys)
        
    async def explain(self, question, answer, explanation=None, feedback_history=None, thread_id=None):
        return self.teach(
            question=question,
            answer=answer,
            explanation=explanation,
            feedback_history=feedback_history,
            thread_id=thread_id
        )
