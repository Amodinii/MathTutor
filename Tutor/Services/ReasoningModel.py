import re
import sys
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder

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

            # Use ChatPromptTemplate with structured messages
            system_message = '''
                You are an expert in solving mathematical questions with precision using formal methods. Your main focus involves solving math problems accurately using those formal methods.
                You will be provided a mathematical question that is being asked in an exam, and your task is to to solve the particular question, and provide the final answer as well as the entire solution for the question.
                Keep in mind, that the solution you will give will be submitted in an exam, where the marks will be calculated based on the accuracy of the solution.
                There will be partial marking for the step-by-step solution of the question, hence ensure to explain each step clearly.
                You will provide you response in an JSON format, where the keys are "reason" and "correct_answer".
                You will provide the entire solution for the question in "reason" and the correct and final answer in "correct_answer".

                So your task is the following:
                1. Solve the mathematical question completely and get an answer.
                2. Provide the entire solution for the question in "reason".
                3. Provide the correct and final answer in "correct_answer".

                Along with this, you will also be provided some documents, which will be useful to you in solving the question. You should use these documents to answer the question, incase you find any information in the documents that can help you answer the question.
            '''
            human_message = "The mathematical question is {question}, and the documents are {documents}."

            # Use ChatPromptTemplate with string-based message types
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", system_message),
                ("human", human_message)
            ])
            logger.info(f"Reasoning model {model_name} initialized successfully with Groq.")

        except Exception as e:
            logger.error("Error initializing reasoning model.")
            raise TutorException(e, sys)

    def retrieve_documents(self, question: str):
        try:
            docs = self.vector_db.retrieve(query=question, threshold=0.5, num_results=5)
            return docs
        except Exception as e:
            logger.error("Error retrieving documents.")
            raise TutorException(e, sys)

    def reason(self, question: str):
        try:
            docs = self.retrieve_documents(question)
            chain = self.prompt | self.llm | self.parser
            model_response = chain.invoke({"question": question, "documents": docs})
            return model_response
        except Exception as e:
            logger.error("Error reasoning with Groq.")
            raise TutorException(e, sys)
