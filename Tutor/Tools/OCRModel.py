import sys
from PIL import Image
from Tutor.Logging.Logger import logger
from Tutor.Exception.Exception import TutorException
from transformers import TrOCRProcessor, VisionEncoderDecoderModel
from langchain_core.tools import tool


class OCRModel:
    def __init__(self):
        try:
            # Load the OCR model and processor
            self.processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
            self.model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")
            logger.info("OCR model initialized successfully.")
        except Exception as e:
            logger.error("Error initializing OCR model.")
            raise TutorException(e, sys)

    
    def get_text(self, image: Image.Image) -> str:
        try:
            if image is None:
                raise ValueError("Image cannot be None.")
            if not isinstance(image, Image.Image):
                raise TypeError("Provided input is not a valid image. Expected PIL Image.")
            
            logger.info("Processing image for OCR...")
            
            # Process the image
            pixel_values = self.processor(image, return_tensors="pt").pixel_values
            
            # Generate text from the image
            generated_ids = self.model.generate(pixel_values)
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
            logger.info("OCR processing completed, text extracted successfully.")
            return generated_text

        except ValueError as ve:
            logger.error(f"Image processing error: {ve}")
            raise TutorException(ve, sys)
        except TypeError as te:
            logger.error(f"Invalid image type: {te}")
            raise TutorException(te, sys)
        except Exception as e:
            logger.error("Error processing image for OCR.")
            raise TutorException(e, sys)