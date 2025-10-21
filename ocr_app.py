import os
from pdf2image import convert_from_path
import io
import yaml
from datetime import datetime
from ocr_services import get_ocr_service


# Helper function to check if a command exists
def command_exists(cmd):
    return os.system(f"type {cmd} > /dev/null 2>&1") == 0



from ocr_services import get_ocr_service

def process_pdf(file_path, service, config):
    """
    Converts a PDF to images and performs OCR on each page.
    """
    if not command_exists("pdftoppm"):
        logger.error("[Error] Poppler is not installed or not in your PATH.")
        logger.error("Please install it. On macOS with Homebrew: brew install poppler")
        return

    logger.info(f"Processing {file_path} with {service}...")

    try:
        ocr_service = get_ocr_service(service, config)
    except ValueError as e:
        logger.error(f"Error: {e}")
        return

    try:
        images = convert_from_path(file_path)
    except Exception as e:
        logger.exception(f"Error converting PDF to images: {e}")
        return

    full_text = ""
    for i, image in enumerate(images):
        logger.info(f"  - Processing page {i + 1}/{len(images)}...")

        # Convert PIL image to bytes for the APIs
        with io.BytesIO() as output:
            image.save(output, format="PNG")
            image_bytes = output.getvalue()

        try:
            text = ocr_service.ocr(image_bytes)
            full_text += f"-------- Page {i + 1} --------\n{text}\n\n"
        except Exception as e:
            logger.exception(f"    [Error on page {i+1}] Could not process page. Error: {e}")

    output_dir = os.path.dirname(file_path) if not config.get("output_file_path") else config.get("output_file_path")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Derive output filename from input PDF name and timestamp
    pdf_base_name = os.path.splitext(os.path.basename(file_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{pdf_base_name}_{timestamp}.md"
    final_output_path = os.path.join(output_dir, output_filename)

    if final_output_path:
        try:
            with open(final_output_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            logger.info(f"\nOCR results saved to {final_output_path}")
        except Exception as e:
            logger.exception(f"\nError saving OCR results to file: {e}")
            logger.info("\n--- Full Extracted Text (printed to console due to file error) ---")
            logger.info(full_text)
    else:
        logger.info("\n--- Full Extracted Text ---")
        logger.info(full_text)

def process_image(file_path, service, config):
    """
    Performs OCR on a single image file.
    """
    logger.info(f"Processing {file_path} with {service}...")

    try:
        ocr_service = get_ocr_service(service, config)
    except ValueError as e:
        logger.error(f"Error: {e}")
        return

    try:
        with open(file_path, "rb") as f:
            image_bytes = f.read()
    except Exception as e:
        logger.exception(f"Error reading image file: {e}")
        return

    full_text = ""
    try:
        text = ocr_service.ocr(image_bytes)
        full_text += f"-------- Image OCR Result --------\n{text}\n\n"
    except Exception as e:
        logger.exception(f"    [Error processing image] Could not process image. Error: {e}")

    output_dir = os.path.dirname(file_path) if not config.get("output_file_path") else config.get("output_file_path")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Derive output filename from input image name and timestamp
    image_base_name = os.path.splitext(os.path.basename(file_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{image_base_name}_{timestamp}.md"
    final_output_path = os.path.join(output_dir, output_filename)

    if final_output_path:
        try:
            with open(final_output_path, "w", encoding="utf-8") as f:
                f.write(full_text)
            logger.info(f"\nOCR results saved to {final_output_path}")
        except Exception as e:
            logger.exception(f"\nError saving OCR results to file: {e}")
            logger.info("\n--- Full Extracted Text (printed to console due to file error) ---")
            logger.info(full_text)
    else:
        logger.info("\n--- Full Extracted Text ---")
        logger.info(full_text)


def load_config(config_path="config.yaml"):
    """Loads configuration from a YAML file."""
    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            if not config or "service" not in config:
                logger.error(
                    "Config file must contain 'service' key. 'output_file_path' is optional."
                )
                return None
            if config["service"] == "azure":
                if "azure_endpoint" not in config or "azure_key" not in config:
                    logger.error(
                        "Config file must contain 'azure_endpoint' and 'azure_key' keys when service is azure."
                    )
                    return None
            elif config["service"] == "google":
                if "google_credentials_path" not in config:
                    logger.warning("Warning: google_credentials_path not found in config.yaml. Attempting to use Application Default Credentials.")
            return config
    except FileNotFoundError:
        logger.error(f"[Error] Configuration file not found at {config_path}")
        return None
    except Exception as e:
        logger.exception(f"[Error] Failed to read or parse config file: {e}")
        return None


import argparse
import logging

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Console Application Call Examples:
#
# To process a single file:
# python ocr_app.py -f /path/to/your/document.pdf
# python ocr_app.py --file /path/to/your/image.png
#
# To process all supported files in a folder:
# python ocr_app.py -fd /path/to/your/folder
# python ocr_app.py --file_folder /path/to/your/another_folder

def main():
    """Main function to load config and process PDF/image."""
    parser = argparse.ArgumentParser(description="Process PDF or image files with OCR.")
    parser.add_argument("-f", "--file", type=str, help="Path to the input PDF or image file.")
    parser.add_argument("-fd", "--file_folder", type=str, help="Path to a folder containing PDF or image files to process.")
    args = parser.parse_args()

    config = load_config()
    if not config:
        return

    # Setup logging based on config
    log_enabled = config.get("log_enabled", True)
    if log_enabled:
        log_directory = config.get("log_directory")
        if not log_directory:
            # Default to output directory if log_directory is not specified
            # If output_file_path is also not specified, default to current working directory
            log_directory = config.get("output_file_path") or os.getcwd()

        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = os.path.join(log_directory, f"ocr_app_{timestamp}.log")

        file_handler = logging.FileHandler(log_filename, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)

    # Also log to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

    service = config.get("service")

    if args.file and args.file_folder:
        logger.error("Error: Please specify either a single --file or a --file_folder, but not both.")
        return
    elif args.file:
        input_path = args.file
        if not os.path.exists(input_path):
            logger.error(f"Error: File not found at {input_path}")
            return

        file_extension = os.path.splitext(input_path)[1].lower()

        if file_extension == ".pdf":
            process_pdf(input_path, service, config)
        elif file_extension in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"]:
            process_image(input_path, service, config)
        else:
            logger.error(f"Error: Unsupported file type '{file_extension}'. Only PDF and image files are supported.")
    elif args.file_folder:
        folder_path = args.file_folder
        if not os.path.isdir(folder_path):
            logger.error(f"Error: Folder not found at {folder_path}")
            return

        logger.info(f"Processing all supported files in folder: {folder_path}")
        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isfile(item_path):
                file_extension = os.path.splitext(item_path)[1].lower()
                if file_extension == ".pdf":
                    process_pdf(item_path, service, config)
                elif file_extension in [".png", ".jpg", ".jpeg", ".gif", ".bmp", ".tiff", ".webp"]:
                    process_image(item_path, service, config)
                else:
                    logger.info(f"Skipping unsupported file: {item_path}")
    else:
        logger.error("Error: Please specify either a file_path or a --folder to process.")


if __name__ == "__main__":
    main()