import sys
import json
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException
from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class ScrapedQA(BaseModel):
    question: str = Field(description="The extracted math question from the document.")
    answer: str = Field(description="The correct answer in LaTeX if needed, along with the explanation, if provided.")
    difficulty: str = Field(description="The difficulty level: easy, medium, or hard.")
    topic: str = Field(
        description="The topic category: one of ['counting and probability', 'algebra', 'geometry', 'intermediate algebra', 'precalculus', 'prealgebra', 'number theory']"
    )


class ScrapeLLM:
    def __init__(self, model_name: str):
        try:
            self.llm = ChatGroq(
                model=model_name,           
                temperature=0.3,
                max_retries=2
            )

            self.parser = JsonOutputParser(pydantic_object=ScrapedQA)

            system_message = """
                You are an expert mathematical content extractor. Your job is to read the provided content,
                find the main math question, solve it accurately, and categorize it.

                Return the result in a JSON format, with the following keys:
                    "question": "Extracted math question text",
                    "answer": "Final answer in LaTeX or plain text, along with the explanation, if provided",
                    "difficulty": "easy | medium | hard",
                    "topic": "One of: counting and probability, algebra, geometry, intermediate algebra, precalculus, prealgebra, number theory"

                Wrap your response exactly in a JSON code block (no commentary).
            """

            human_message = "Extract and solve the math problem in this content:\n{document}"

            self.prompt = ChatPromptTemplate.from_messages([
                ("system", system_message),
                ("human", human_message)
            ])

            logger.info(f"[ScrapeLLM] Model {model_name} initialized with parser.")

        except Exception as e:
            logger.error("[ScrapeLLM] Error initializing scrape model.")
            raise TutorException(e, sys)

    async def extract(self, document: str):
        try:
            chain = self.prompt | self.llm
            result = await chain.ainvoke({"document": document})
            cleaned_content = result.content.strip("`\n")
            parsed_result = json.loads(cleaned_content)
            return parsed_result
        except Exception as e:
            logger.error("[ScrapeLLM] Error extracting from document.")
            raise TutorException(e, sys)