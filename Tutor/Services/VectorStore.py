import os
import sys
from uuid import uuid4
from langchain_astradb import AstraDBVectorStore
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException
from Tutor.Services.EmbeddingModel import EmbeddingModel

class VectorStore:
    def __init__(self, model_name: str):
        try:
            self.embedding_model = EmbeddingModel(model_name=model_name)
            self.vector_store = AstraDBVectorStore(
                collection_name = "tutor",
                embedding = self.embedding_model,
                api_endpoint=os.getenv("ASTRA_DB_API_ENDPOINT"),
                token=os.getenv("ASTRA_DB_TOKEN"),
            )
            logger.info("Vector store initialized successfully.")
        except Exception as e:
            logger.error("Error initializing vector store.")
            raise TutorException(e, sys)

    def add_documents(self, documents):
        try:
            if not documents:
                raise ValueError("No documents to add.")
            uuids = [str(uuid4()) for _ in range(len(documents))]
            self.vector_store.add_documents(documents=documents, ids=uuids)
            logger.info(f"Added {len(documents)} documents to the vector store.")
        except ValueError as ve:
            logger.error(f"Adding documents error: {ve}")
            raise TutorException(ve, sys)
        except Exception as e:
            logger.error("Error adding documents to vector store.")
            raise TutorException(e, sys)

    def retrieve(self, query, threshold, num_results):
        try:
            retriever = self.vector_store.as_retriever(
                search_type="similarity_score_threshold",
                search_kwargs={"k": num_results, "score_threshold": threshold},
            )
            results = retriever.invoke(query)
            logger.info(f"Performed retrieval for query with score threshold {threshold}")
            return results
        except Exception as e:
            logger.error(f"Error retrieving documents for query: {query}")
            raise TutorException(e, sys)