import pdfplumber
import argparse
from datetime import datetime
import os

import re

def pdf_to_markdown(pdf_path, output_path, title_recognize, color_recognize, header_regex, footer_regex):
    """
    Converts a text-based PDF to a Markdown file, preserving headings and text styles.
    """
    with pdfplumber.open(pdf_path) as pdf:
        markdown_content = ""
        for page in pdf.pages:
            markdown_content += f"\n\n<!-- Page {page.page_number} -->\n\n"
            
            # Sort characters by vertical position, then horizontal
            sorted_chars = sorted(page.chars, key=lambda c: (c["top"], c["x0"]))

            # Group characters into lines with a dynamic tolerance
            lines = []
            if sorted_chars:
                current_line = [sorted_chars[0]]
                for char in sorted_chars[1:]:
                    tolerance = current_line[-1]["size"] * 0.2
                    if abs(char["top"] - current_line[-1]["top"]) < tolerance:
                        current_line.append(char)
                    else:
                        lines.append(current_line)
                        current_line = [char]
                lines.append(current_line)

            # Filter out headers and footers
            if header_regex:
                lines = [line for line in lines if not re.match(header_regex, "".join([char["text"] for char in line]).strip())]
            if footer_regex:
                lines = [line for line in lines if not re.match(footer_regex, "".join([char["text"] for char in line]).strip())]

            # First pass: Analyze lines and create line objects
            line_objects = []
            for line in lines:
                line_text = ""
                is_heading = False
                heading_level = 0
                line_color = None

                styled_chars = {}
                for char in line:
                    fontname = char.get("fontname", "").lower()
                    size = round(char.get("size", 0))
                    color = char.get("non_stroking_color", (0, 0, 0))
                    style = (fontname, size, color)
                    if style not in styled_chars:
                        styled_chars[style] = []
                    styled_chars[style].append(char["text"])

                if title_recognize and len(styled_chars) == 1:
                    fontname, size, color = list(styled_chars.keys())[0]
                    if "bold" in fontname and size > 14:
                        is_heading = True
                        heading_level = 1 if size > 18 else 2
                        line_color = color

                for style, texts in styled_chars.items():
                    text = "".join(texts)
                    if color_recognize:
                        fontname, size, color = style
                        is_bold = "bold" in fontname
                        is_italic = "italic" in fontname or "oblique" in fontname
                        if is_bold:
                            text = f"**{text}**"
                        if is_italic:
                            text = f"*{text}*"
                        if color != (0, 0, 0):
                            hex_color = f"#{int(color[0]*255):02x}{int(color[1]*255):02x}{int(color[2]*255):02x}"
                            text = f'<font color="{hex_color}">{text}</font>'
                    line_text += text
                
                line_objects.append({
                    "text": line_text,
                    "is_heading": is_heading,
                    "heading_level": heading_level,
                    "color": line_color
                })

            # Second pass: Merge consecutive titles
            merged_lines = []
            i = 0
            while i < len(line_objects):
                current_line = line_objects[i]
                if title_recognize and current_line["is_heading"] and i + 1 < len(line_objects):
                    next_line = line_objects[i+1]
                    if (
                        next_line["is_heading"]
                        and current_line["heading_level"] == next_line["heading_level"]
                        and current_line["color"] == next_line["color"]
                    ):
                        current_line["text"] += " " + next_line["text"]
                        i += 1  # Skip the next line as it has been merged
                merged_lines.append(current_line)
                i += 1

            # Final pass: Generate Markdown
            for line in merged_lines:
                if title_recognize and line["is_heading"]:
                    markdown_content += f"{'#' * line['heading_level']} {line['text']}\n"
                else:
                    markdown_content += line["text"] + "\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    print(f"Successfully converted {pdf_path} to {output_path}")

# Console Application Call Examples:
#
# To convert a PDF to Markdown with basic text extraction (no title or style recognition):
# python pdf_to_markdown.py -f /path/to/your/document.pdf
#
# To convert a PDF to Markdown with title recognition enabled:
# python pdf_to_markdown.py -f /path/to/your/document.pdf -tr
# python pdf_to_markdown.py -f /path/to/your/document.pdf --title_recognize
#
# To convert a PDF to Markdown with color and style (bold/italic) recognition enabled:
# python pdf_to_markdown.py -f /path/to/your/document.pdf -cr
# python pdf_to_markdown.py -f /path/to/your/document.pdf --color_recognize
#
# To convert a PDF to Markdown with both title and color/style recognition enabled:
# python pdf_to_markdown.py -f /path/to/your/document.pdf -tr -cr
# python pdf_to_markdown.py -f /path/to/your/document.pdf --title_recognize --color_recognize

def main():
    """
    Main function to parse arguments and run the conversion.
    """
    parser = argparse.ArgumentParser(description="Convert a text-based PDF to a Markdown file.")
    parser.add_argument("-f", "--file", type=str, required=True, help="Path to the input PDF file.")
    parser.add_argument("-tr", "--title_recognize", action="store_true", help="Enable title recognition.")
    parser.add_argument("-cr", "--color_recognize", action="store_true", help="Enable color and style recognition.")
    parser.add_argument("--header_regex", type=str, help="Regular expression to identify and remove headers.")
    parser.add_argument("--footer_regex", type=str, help="Regular expression to identify and remove footers.")
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

    pdf_to_markdown(pdf_path, output_path, args.title_recognize, args.color_recognize, args.header_regex, args.footer_regex)

if __name__ == "__main__":
    main()