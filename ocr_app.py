import os
from pdf2image import convert_from_path
import io
import yaml
from datetime import datetime


# Helper function to check if a command exists
def command_exists(cmd):
    return os.system(f"type {cmd} > /dev/null 2>&1") == 0


# --- Google Cloud Vision ---
def ocr_google(image_bytes, config):
    """Performs OCR using Google Cloud Vision API."""
    try:
        from google.cloud import vision
        from google.oauth2 import service_account
    except ImportError:
        return "[Error] Google Cloud Vision library not installed. Please run: pip install google-cloud-vision"

    credentials_path = config.get("google_credentials_path")
    if credentials_path:
        try:
            credentials = service_account.Credentials.from_service_account_file(credentials_path)
            client = vision.ImageAnnotatorClient(credentials=credentials)
        except Exception as e:
            return f"[Error] Failed to load Google Cloud credentials from {credentials_path}: {e}"
    else:
        client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description
    return ""


# --- Azure AI Vision ---
def ocr_azure(image_bytes, config):
    """Performs OCR using Azure AI Vision."""
    try:
        from azure.ai.vision.imageanalysis import ImageAnalysisClient
        from azure.core.credentials import AzureKeyCredential
    except ImportError:
        return "[Error] Azure AI Vision library not installed. Please run: pip install azure-ai-vision-imageanalysis"

    try:
        endpoint = config["azure_endpoint"]
        key = config["azure_key"]
    except KeyError:
        return "[Error] Please set azure_endpoint and azure_key in config.yaml."

    client = ImageAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    result = client.analyze(image_data=image_bytes, visual_features=["read"])

    if result.read and result.read.blocks:
        return "\n".join(
            [line.text for block in result.read.blocks for line in block.lines]
        )
    return ""


# --- AWS Textract ---
def ocr_aws(image_bytes, config):
    """Performs OCR using AWS Textract."""
    try:
        import boto3
    except ImportError:
        return "[Error] AWS SDK for Python (boto3) not installed. Please run: pip install boto3"

    try:
        # It's recommended to configure region via ~/.aws/config or AWS_REGION env var
        textract = boto3.client("textract")
    except Exception as e:
        return f"[Error] Failed to create AWS Textract client: {e}"

    response = textract.detect_document_text(Document={"Bytes": image_bytes})

    text = []
    for item in response["Blocks"]:
        if item["BlockType"] == "LINE":
            text.append(item["Text"])
    return "\n".join(text)

def process_pdf(file_path, service, config):
    """
    Converts a PDF to images and performs OCR on each page.
    """
    if not command_exists("pdftoppm"):
        print("[Error] Poppler is not installed or not in your PATH.")
        print("Please install it. On macOS with Homebrew: brew install poppler")
        return

    print(f"Processing {file_path} with {service}...")

    ocr_functions = {
        "google": ocr_google,
        "azure": ocr_azure,
        "aws": ocr_aws,
    }

    if service not in ocr_functions:
        print(
            f"Error: Service '{service}' is not supported. Choose from {list(ocr_functions.keys())}"
        )
        return

    try:
        images = convert_from_path(file_path)
    except Exception as e:
        print(f"Error converting PDF to images: {e}")
        return

    full_text = ""
    for i, image in enumerate(images):
        print(f"  - Processing page {i + 1}/{len(images)}...")

        # Convert PIL image to bytes for the APIs
        with io.BytesIO() as output:
            image.save(output, format="PNG")
            image_bytes = output.getvalue()

        try:
            text = ocr_functions[service](image_bytes, config)
            full_text += f"-------- Page {i + 1} --------\n{text}\n\n"
        except Exception as e:
            print(f"    [Error on page {i+1}] Could not process page. Error: {e}")

    output_file_path = config.get("output_file_path")

    if output_file_path:
        try:
            # Add timestamp to the output filename
            base, ext = os.path.splitext(output_file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            timestamped_output_file_path = f"{base}_{timestamp}{ext}"

            with open(timestamped_output_file_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            print(f"\nOCR results saved to {timestamped_output_file_path}")
        except Exception as e:
            print(f"\nError saving OCR results to file: {e}")
            print("\n--- Full Extracted Text (printed to console due to file error) ---")
            print(full_text)
    else:
        print("\n--- Full Extracted Text ---")
        print(full_text)


def load_config(config_path="config.yaml"):
    """Loads configuration from a YAML file."""
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            if not config or "service" not in config or "pdf_file_path" not in config:
                raise ValueError(
                    "Config file must contain 'service' and 'pdf_file_path' keys. 'output_file_path' is optional."
                )
            if config["service"] == "azure":
                if "azure_endpoint" not in config or "azure_key" not in config:
                    raise ValueError(
                        "Config file must contain 'azure_endpoint' and 'azure_key' keys when service is azure."
                    )
            elif config["service"] == "google":
                if "google_credentials_path" not in config:
                    print("Warning: google_credentials_path not found in config.yaml. Attempting to use Application Default Credentials.")
            return config
    except FileNotFoundError:
        print(f"[Error] Configuration file not found at {config_path}")
        return None
    except Exception as e:
        print(f"[Error] Failed to read or parse config file: {e}")
        return None


def main():
    """Main function to load config and process PDF."""
    config = load_config()
    if not config:
        return

    service = config.get("service")
    file_path = config.get("pdf_file_path")

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return

    process_pdf(file_path, service, config)


if __name__ == "__main__":
    main()