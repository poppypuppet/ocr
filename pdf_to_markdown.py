import pdfplumber
import argparse
from datetime import datetime
import os

def pdf_to_markdown(pdf_path, output_path):
    """
    Converts a text-based PDF to a Markdown file, preserving headings.
    """
    with pdfplumber.open(pdf_path) as pdf:
        markdown_content = ""
        all_words = []
        # First pass to collect all words and identify font sizes and their frequencies
        font_sizes = {}
        for page in pdf.pages:
            words_on_page = page.extract_words()
            all_words.extend(words_on_page)
            for obj in words_on_page:
                if "size" in obj:
                    size = round(obj["size"])
                    if size in font_sizes:
                        font_sizes[size] += 1
                    else:
                        font_sizes[size] = 1

        if not font_sizes:
            print("No font size information found in structured text, falling back to plain text extraction.")
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    markdown_content += text + "\n"
        else:
            # Identify heading sizes based on frequency
            sorted_sizes = sorted(font_sizes.items(), key=lambda item: item[1], reverse=True)
            body_size = sorted_sizes[0][0]
            heading_sizes = sorted([size for size, freq in font_sizes.items() if size > body_size], reverse=True)

            heading_levels = {size: i + 1 for i, size in enumerate(heading_sizes)}

            # Second pass to generate Markdown
            current_page_number = 0
            for obj in all_words:
                if obj["page_number"] != current_page_number:
                    markdown_content += f"\n\n<!-- Page {obj["page_number"]} -->\n\n"
                    current_page_number = obj["page_number"]

                text = obj["text"]
                if "size" in obj and obj["size"] in heading_levels:
                    level = heading_levels[obj["size"]]
                    markdown_content += f"{ '#' * level} {text} "
                else:
                    markdown_content += f"{text} "
            markdown_content += "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    print(f"Successfully converted {pdf_path} to {output_path}")

def main():
    """
    Main function to parse arguments and run the conversion.
    """
    parser = argparse.ArgumentParser(description="Convert a text-based PDF to a Markdown file.")
    parser.add_argument("-f", "--file", type=str, required=True, help="Path to the input PDF file.")
    args = parser.parse_args()

    pdf_path = args.file
    if not os.path.exists(pdf_path):
        print(f"Error: File not found at {pdf_path}")
        return

    # Derive output filename from input PDF name and timestamp
    pdf_base_name = os.path.splitext(os.path.basename(pdf_path))[0]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"{pdf_base_name}_{timestamp}.md"
    output_dir = os.path.dirname(pdf_path)
    output_path = os.path.join(output_dir, output_filename)

    pdf_to_markdown(pdf_path, output_path)

if __name__ == "__main__":
    main()