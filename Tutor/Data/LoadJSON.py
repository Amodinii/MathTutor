import os
import json
import sys

from langchain_core.documents import Document
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

class LoadJSON:
    @staticmethod
    def load_documents(directory_path):
        try:
            docs = []
            for filename in os.listdir(directory_path):
                logger.info(f"Loading file: {filename}")
                if not filename.endswith(".json"):
                    logger.warning(f"Skipping non-JSON file: {filename}")
                    continue
                if filename.endswith(".json"):
                    file_path = os.path.join(directory_path, filename)
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        problem = data.get("problem")
                        solution = data.get("solution")
                        if problem and solution:
                            content = f"Problem: {problem}\nSolution: {solution}"
                            logger.info(f"Loaded content from {filename}: {content}")
                            docs.append(Document(page_content=content, metadata={"source": filename}))
            return docs
        except Exception as e:
            logger.error(f"Error loading JSON files: {e}")
            raise TutorException(e,sys)