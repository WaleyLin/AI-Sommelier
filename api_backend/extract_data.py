# Extracts text data from PDF files.
# Prepares the extracted data for indexing and embedding.

import os
import pdfplumber
import json

# Paths
PDF_FOLDER = "./data/pdfs"  # Path to the folder containing PDFs
OUTPUT_FILE = "./data/extracted_data.json"  # Path to save the extracted text as JSON

def extract_pdf_text(file_path):
    """Extract text from a single PDF."""
    with pdfplumber.open(file_path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        return text.strip()

def process_pdfs():
    """Process all PDFs in the specified folder and save extracted text to JSON."""
    if not os.path.exists(PDF_FOLDER):
        raise FileNotFoundError(f"PDF folder not found: {PDF_FOLDER}")

    data = {}

    for pdf_file in os.listdir(PDF_FOLDER):
        if pdf_file.endswith(".pdf"):
            file_path = os.path.join(PDF_FOLDER, pdf_file)
            print(f"Processing {pdf_file}...")
            text = extract_pdf_text(file_path)
            data[pdf_file] = text

    # Ensure output folder exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Save extracted data to JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"Data extracted and saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    process_pdfs()