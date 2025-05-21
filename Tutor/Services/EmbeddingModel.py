import os
import sys
from dotenv import load_dotenv
load_dotenv()

from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

class EmbeddingModel:
    def __init__(self, model_name: str):
        try:
            if not model_name:
                raise ValueError("Model name cannot be empty.")
            
            if not os.getenv("HUGGINGFACE_ACCESS_TOKEN"):
                raise ValueError("HUGGINGFACE_ACCESS_TOKEN environment variable is not set.")
            
            self.model_name = model_name
            self.embeddings = HuggingFaceInferenceAPIEmbeddings(
                model_name=model_name,
                api_key=os.getenv("HUGGINGFACE_ACCESS_TOKEN")
            )
            logger.info(f"Embedding model '{model_name}' initialized successfully.")
        except ValueError as ve:
            logger.error(f"Initialization error: {ve}")
            raise TutorException(ve, sys)
        except Exception as e:
            logger.error(f"Error initializing embedding model '{model_name}'.")
            raise TutorException(e, sys)

    def embed_query(self, text: str):
        try:
            if not text or text.strip() == "":
                raise ValueError("Text to embed cannot be empty or just whitespace.")
            logger.info(f"Embedding text: {text[:30]}...")
            return self.embeddings.embed_query(text=text)

        except ValueError as ve:
            logger.error(f"Embedding error: {ve}") 
            raise TutorException(ve, sys)
        except Exception as e:
            logger.error("Error embedding text...")
            raise TutorException(e, sys)
        
    def embed_documents(self, texts: list):
        try:
            if not texts:
                raise ValueError("List of texts to embed cannot be empty.")
            
            logger.info(f"Embedding {len(texts)} documents...")
            return self.embeddings.embed_documents(texts)
        except ValueError as ve:
            logger.error(f"Embedding documents error: {ve}")
            raise TutorException(ve, sys)
        except Exception as e:
            logger.error("Error embedding documents...")
            raise TutorException(e, sys)
