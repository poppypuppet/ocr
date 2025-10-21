from .ocr_base import OcrService

def get_ocr_service(service_name: str, config: dict) -> OcrService:
    """
    Factory function to get an instance of the specified OCR service.

    :param service_name: The name of the service to use (e.g., 'google', 'azure', 'aws').
    :param config: The configuration dictionary.
    :return: An instance of the OCR service.
    """
    if service_name == "google":
        from .ocr_google import GoogleOcrService
        return GoogleOcrService(config)
    elif service_name == "azure":
        from .ocr_azure import AzureOcrService
        return AzureOcrService(config)
    elif service_name == "aws":
        from .ocr_aws import AwsOcrService
        return AwsOcrService(config)
    else:
        raise ValueError(f"Unsupported OCR service: {service_name}")
