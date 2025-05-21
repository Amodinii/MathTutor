import sys
import os
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException
from Tutor.Data.LoadJSON import LoadJSON
from Tutor.Services.VectorStore import VectorStore

class PushToDB:
    def __init__(self, vector_store):
        try:
            if not isinstance(vector_store, VectorStore):
                raise ValueError("vector_store must be an instance of VectorStore")
            self.vector_store = vector_store
        except Exception as e:
            logger.error(f"Error initializing PushToDB: {e}")
            raise TutorException(e, sys)


    def push_to_db(self,directory_path):
        try:
            logger.info("Loading documents from JSON files...")
            docs = LoadJSON.load_documents(directory_path)
            logger.info(f"Loaded {len(docs)} documents.")
            
            logger.info("Pushing documents to vector store...")
            vector_store = VectorStore()
            vector_store.add_documents(docs)
            logger.info("Documents pushed to vector store successfully.")
        except Exception as e:
            logger.error(f"Error pushing documents to DB: {e}")
            raise TutorException(e, sys)
