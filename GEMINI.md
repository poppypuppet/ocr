# GEMINI.md

## Project Overview

This project contains a Python command-line interface (CLI) tool, `ocr_app.py`, designed to extract text from image-based PDF files. It leverages various cloud Optical Character Recognition (OCR) services to perform the text extraction.

The script is architected to be modular, with support for different OCR providers that can be selected via a command-line argument. It processes multi-page PDFs by converting each page to an image and running OCR on it individually.

**Key Technologies:**
*   Python 3
*   `argparse` for CLI argument parsing
*   `pdf2image` for PDF to image conversion
*   `Pillow (PIL)` for image handling
*   Supported OCR Services:
    *   Google Cloud Vision API
    *   Azure AI Vision
    *   Amazon Textract

## Building and Running

### 1. Prerequisites

Before running the script, you need to install the `poppler` utility, which is a dependency for `pdf2image`.

*   **On macOS (using Homebrew):**
    ```bash
    brew install poppler
    ```
*   **On Debian/Ubuntu:**
    ```bash
    sudo apt-get install poppler-utils
    ```

### 2. Python Dependencies

The script requires several Python packages. You only need to install the package for the specific OCR service you intend to use.

*   **For Google Cloud Vision:**
    ```bash
    pip install google-cloud-vision pdf2image Pillow
    ```
*   **For Azure AI Vision:**
    ```bash
    pip install azure-ai-vision-imageanalysis pdf2image Pillow
    ```
*   **For AWS Textract:**
    ```bash
    pip install boto3 pdf2image Pillow
    ```

### 3. Cloud Service Configuration

You must configure credentials for the cloud service you wish to use.

*   **Google Cloud:**
    Ensure your environment is authenticated. The common method is to use the `gcloud` CLI:
    ```bash
    gcloud auth application-default login
    ```

*   **Azure:**
    Set the following environment variables with your Azure AI Vision credentials:
    ```bash
    export AZURE_VISION_ENDPOINT="YOUR_ENDPOINT_HERE"
    export AZURE_VISION_KEY="YOUR_KEY_HERE"
    ```

*   **AWS:**
    Configure your AWS credentials, typically via the `~/.aws/credentials` and `~/.aws/config` files or by setting environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`).

### 4. Running the Script

To run the OCR process, use the following command, specifying the path to your PDF and the desired service.

```bash
python ocr_app.py --file /path/to/your/document.pdf --service <google|azure|aws>
```

**Example:**
```bash
python ocr_app.py --file my_scanned_doc.pdf --service google
```

## Development Conventions

*   **Modular Design:** Each OCR service is implemented in its own function (`ocr_google`, `ocr_azure`, `ocr_aws`). This makes it easy to add new services in the future.
*   **Clear CLI:** The script uses the `argparse` library to provide a clean and self-documenting command-line interface.
*   **Error Handling:** The script includes checks for missing dependencies and environment variables to provide clear feedback to the user.
*   **Dependency Management:** Python dependencies are imported within their respective functions, allowing the script to run even if only one of the cloud SDKs is installed.
