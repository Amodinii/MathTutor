import sys
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain.prompts.chat import ChatPromptTemplate

class ReasoningModel:
    def __init__(self, model_name: str):
        try:
            self.llm = ChatGroq(
                model=model_name,
                temperature=0.3,
                max_retries=2
            )
            system_message = '''
                You are an expert in solving mathematical questions with precision using formal methods. 
                Your main focus involves solving math problems accurately using those formal methods.
                
                You will be provided a mathematical question that is being asked in an exam, and your task 
                is to solve the question and provide the final answer and full reasoning.

                There will be partial marks for clear step-by-step reasoning, so explain each step clearly.

                Use the provided documents if they help.

                Respond in JSON with:
                - "reason": full step-by-step reasoning
                - "correct_answer": final answer
            '''

            human_message = "The mathematical question is {question}, and the documents are {documents}."

            self.prompt = ChatPromptTemplate.from_messages([
                ("system", system_message),
                ("human", human_message)
            ])

            logger.info(f"Reasoning model {model_name} initialized successfully with Groq.")

        except Exception as e:
            logger.error("Error initializing reasoning model.")
            raise TutorException(e, sys)

    async def reason(self, question: str, documents: list):
        try:
            chain = self.prompt | self.llm
            response = await chain.ainvoke({
                "question": question,
                "documents": documents
            })
            return response
        except Exception as e:
            logger.error("Error reasoning with Groq.")
            raise TutorException(e, sys)