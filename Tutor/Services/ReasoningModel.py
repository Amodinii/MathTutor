import re
import sys
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from langchain.prompts.chat import ChatPromptTemplate


class Response(BaseModel):
    reason: str = Field(description="The mathematical reasoning done to solve the question")
    correct_answer: str = Field(description="Answer to the question")


class ReasoningModel:
    def __init__(self, model_name: str, vector_db):
        try:
            self.vector_db = vector_db

            self.llm = ChatGroq(
                model=model_name,
                temperature=0.3,
                max_retries=2
            )

            self.parser = JsonOutputParser(pydantic_object=Response)

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

    async def retrieve_documents(self, question: str):
        try:
            docs = await self.vector_db.retrieve_documents(query=question, threshold=0.5, num_results=5)
            return docs
        except Exception as e:
            logger.error("Error retrieving documents.")
            raise TutorException(e, sys)

    async def reason(self, question: str):
        try:
            docs = await self.retrieve_documents(question)
            chain = self.prompt | self.llm | self.parser
            response = await chain.ainvoke({"question": question, "documents": docs})
            return response
        except Exception as e:
            logger.error("Error reasoning with Groq.")
            raise TutorException(e, sys)