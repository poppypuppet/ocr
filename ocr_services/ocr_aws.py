import logging
from .ocr_base import OcrService

logger = logging.getLogger(__name__)

class AwsOcrService(OcrService):
    """Performs OCR using AWS Textract."""

    def __init__(self, config):
        try:
            import boto3
        except ImportError:
            logger.error("[Error] AWS SDK for Python (boto3) not installed. Please run: pip install boto3")
            raise

        try:
            # It's recommended to configure region via ~/.aws/config or AWS_REGION env var
            self.textract = boto3.client("textract")
        except Exception as e:
            logger.error(f"[Error] Failed to create AWS Textract client: {e}")
            raise

    def ocr(self, image_bytes: bytes) -> str:
        response = self.textract.detect_document_text(Document={"Bytes": image_bytes})

        text = []
        for item in response["Blocks"]:
            if item["BlockType"] == "LINE":
                text.append(item["Text"])
        return "\n".join(text)
