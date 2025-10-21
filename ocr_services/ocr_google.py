import logging
from .ocr_base import OcrService

logger = logging.getLogger(__name__)

class GoogleOcrService(OcrService):
    """Performs OCR using Google Cloud Vision API."""

    def __init__(self, config):
        try:
            from google.cloud import vision
            from google.oauth2 import service_account
        except ImportError:
            logger.error("[Error] Google Cloud Vision library not installed. Please run: pip install google-cloud-vision")
            raise

        credentials_path = config.get("google_credentials_path")
        if credentials_path:
            try:
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                self.client = vision.ImageAnnotatorClient(credentials=credentials)
            except Exception as e:
                logger.error(f"[Error] Failed to load Google Cloud credentials from {credentials_path}: {e}")
                raise
        else:
            self.client = vision.ImageAnnotatorClient()

    def ocr(self, image_bytes: bytes) -> str:
        from google.cloud import vision
        image = vision.Image(content=image_bytes)
        response = self.client.text_detection(image=image)
        texts = response.text_annotations
        if texts:
            return texts[0].description
        return ""
