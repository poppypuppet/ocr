from abc import ABC, abstractmethod

class OcrService(ABC):
    """
    Abstract base class for OCR services.
    """

    @abstractmethod
    def ocr(self, image_bytes: bytes) -> str:
        """
        Performs OCR on the given image bytes.

        :param image_bytes: The image data in bytes.
        :return: The extracted text.
        """
        pass
