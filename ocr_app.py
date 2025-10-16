
import argparse
import os
from pdf2image import convert_from_path
from PIL import Image
import io

# Helper function to check if a command exists
def command_exists(cmd):
    return os.system(f"type {cmd} > /dev/null 2>&1") == 0

# --- Google Cloud Vision ---
def ocr_google(image_bytes):
    """Performs OCR using Google Cloud Vision API."""
    try:
        from google.cloud import vision
    except ImportError:
        return "[Error] Google Cloud Vision library not installed. Please run: pip install google-cloud-vision"

    client = vision.ImageAnnotatorClient()
    image = vision.Image(content=image_bytes)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description
    return ""

# --- Azure AI Vision ---
def ocr_azure(image_bytes):
    """Performs OCR using Azure AI Vision."""
    try:
        from azure.ai.vision.imageanalysis import ImageAnalysisClient
        from azure.core.credentials import AzureKeyCredential
    except ImportError:
        return "[Error] Azure AI Vision library not installed. Please run: pip install azure-ai-vision-imageanalysis"

    try:
        endpoint = os.environ["AZURE_VISION_ENDPOINT"]
        key = os.environ["AZURE_VISION_KEY"]
    except KeyError:
        return "[Error] Please set AZURE_VISION_ENDPOINT and AZURE_VISION_KEY environment variables."

    client = ImageAnalysisClient(endpoint=endpoint, credential=AzureKeyCredential(key))
    result = client.analyze(image_data=image_bytes, visual_features=["read"])
    
    if result.read and result.read.blocks:
        return "\n".join([line.text for block in result.read.blocks for line in block.lines])
    return ""

# --- AWS Textract ---
def ocr_aws(image_bytes):
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

    response = textract.detect_document_text(Document={'Bytes': image_bytes})
    
    text = []
    for item in response["Blocks"]:
        if item["BlockType"] == "LINE":
            text.append(item["Text"])
    return "\n".join(text)


def process_pdf(file_path, service):
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
        print(f"Error: Service '{service}' is not supported. Choose from {list(ocr_functions.keys())}")
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
            text = ocr_functions[service](image_bytes)
            full_text += f"--- Page {i + 1} ---\n{text}\n\n"
        except Exception as e:
            print(f"    [Error on page {i+1}] Could not process page. Error: {e}")


    print("\n--- Full Extracted Text ---")
    print(full_text)


def main():
    parser = argparse.ArgumentParser(description="Extract text from an image-based PDF using cloud OCR services.")
    parser.add_argument("--file", type=str, required=True, help="Path to the PDF file.")
    parser.add_argument(
        "--service",
        type=str,
        required=True,
        choices=["google", "azure", "aws"],
        help="The OCR service to use.",
    )
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: File not found at {args.file}")
        return

    process_pdf(args.file, args.service)

if __name__ == "__main__":
    main()
