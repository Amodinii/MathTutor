import sys
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException

class Routing:
    def __init__ (self, vector_store):
        try:
            self.vector_store = vector_store
            logger.info("Routing initialized successfully.")
        except Exception as e:
            logger.error("Error initializing routing.")
            raise TutorException(e, sys)

    def route(self, input_data, threshold, num_results):
        try:
            # Search the vector store for the input data
            results = self.vector_store.retrieve(
                query=input_data, threshold=threshold, num_results=num_results
            )
            if results:
                logger.info(f"Documents found in vector store for input: {input_data}")
                return results, {"route_type" : "Found in DB"}
            else:
                logger.info(f"No documents found in vector store for input: {input_data}")
                return None, {"route_type" : "Not Found in DB"}

        except Exception as e:
            logger.error("Error during searching in vector store.")
            raise TutorException(e, sys)