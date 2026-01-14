import logging
from .ocr_base import OcrService

logger = logging.getLogger(__name__)

class AzureOcrService(OcrService):
    """Performs OCR using Azure AI Vision."""

    def __init__(self, config):
        try:
            from azure.ai.vision.imageanalysis import ImageAnalysisClient
            from azure.core.credentials import AzureKeyCredential
        except ImportError:
            logger.error("[Error] Azure AI Vision library not installed. Please run: pip install azure-ai-vision-imageanalysis")
            raise

        try:
            endpoint = config["azure_endpoint"]
            key = config["azure_key"]
        except KeyError:
            logger.error("[Error] Please set azure_endpoint and azure_key in config.yaml.")
            raise

        self.client = ImageAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))

    def ocr(self, image_bytes: bytes) -> str:
        result = self.client.analyze(image_data=image_bytes, visual_features=["read"])

        if result.read and result.read.blocks:
            return "\n".join(
                [line.text for block in result.read.blocks for line in block.lines]
            )
        return ""
