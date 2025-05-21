import re
import sys
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

from langchain_groq import ChatGroq
from langchain.prompts.chat import ChatPromptTemplate

class TeachingModel:
    def __init__(self, model_name):
        try:
            self.llm = ChatGroq(
                    model=model_name,
                    temperature=0.7,
                    max_retries=2
                )
            system_message = '''

            '''
            human_message = '''
                
            ''' 

            self.prompt = ChatPromptTemplate.from_messages([
                    ("system", system_message),
                    ("human", human_message)
                ])

            logger.info(f"Teaching model {model_name} initialized successfully with Groq.")

        except Exception as e:
            logger.error("Error initializing reasoning model.")
            raise TutorException(e, sys)
    
    def teach(self, question, answer, explanation):
        try:
            chain = self.prompt | self.llm
            model_response = chain.invoke({"question": question, "answer": answer, "explanation": explanation})
            return model_response.content
        except Exception as e:
            logger.error("Error teaching student.")
            raise TutorException(e, sys)