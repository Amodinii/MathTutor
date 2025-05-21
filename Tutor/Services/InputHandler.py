import sys
from PIL import Image
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException
from Tutor.Tools.OCRModel import OCRModel

class InputHandler:
    def __init__(self):
        try:
            logger.info("Input handler initialized successfully.")
        except Exception as e:
            logger.error("Error initializing input handler.")
            raise TutorException(e, sys)

    def check_input_type(self, input_data):
        try:
            if isinstance(input_data, str):  # Text input
                return {"input_type": "text"}
            elif isinstance(input_data, Image.Image):  # Image input
                return {"input_type": "Image"}
            else:
                raise TypeError("Input must be either text or an image.")
        except TypeError as te:
            logger.error(f"Invalid input type: {te}")
            raise TutorException(te, sys)
        except Exception as e:
            logger.error("Error checking input type.")
            raise TutorException(e, sys)