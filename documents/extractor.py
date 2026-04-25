import pdfplumber
import re


def extract_text_from_pdf(file_path):
    """
    Extract text from each page of a PDF file.
    Returns a list of dictionaries with page number and text.
    """
    pages_data = []

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            raw_text = page.extract_text()

            if raw_text:
                cleaned = clean_text(raw_text)
                if cleaned and len(cleaned.split()) > 10:
                    pages_data.append({
                        'page_number': page_num,
                        'text': cleaned
                    })

    return pages_data


def clean_text(text):
    """
    Aggressively clean raw extracted text.

    Removes:
    - Page headers and footers
    - Page number lines
    - Institution name lines
    - Very short meaningless lines
    - Extra whitespace
    - Special characters
    """

    lines = text.split('\n')
    cleaned_lines = []

    # Patterns to remove completely
    noise_patterns = [
        r'^page\s+no\.?\s*[ivxlcdm\d]+',      # Page No.i, Page No.1
        r'^page\s+\d+',                          # Page 1, Page 12
        r'^\s*\d+\s*$',                          # Lines with only numbers
        r'^ccet\s+ips\s*$',                      # CCET IPS
        r'^ccet\s*$',                            # CCET
        r'^ips\s*$',                             # IPS
        r'^askdocs\s+ai\s*$',                    # AskDocs AI alone
        r'^\s*[ivxlcdm]+\s*$',                  # Roman numerals alone
        r'^table\s+of\s+content',               # Table of Content
        r'^sr\.?\s*no\.?\s+contents',           # Sr. No. Contents
        r'^page\s+no\.',                         # Page No.
        r'^\s*[-–—]+\s*$',                      # Lines of dashes only
        r'^\s*[•·●]\s*$',                       # Bullet points alone
    ]

    for line in lines:
        line = line.strip()

        # Skip empty lines
        if not line:
            continue

        # Skip very short lines (less than 3 words)
        if len(line.split()) < 3:
            continue

        # Check against noise patterns
        is_noise = False
        for pattern in noise_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                is_noise = True
                break

        # Skip lines that are mostly numbers and dots (like ToC entries)
        # Example: "Introduction iii-v" or "References xvi"
        if re.match(r'^.{1,40}\s+[ivxlcdm\d]+([-–][ivxlcdm\d]+)?\s*$',
                    line, re.IGNORECASE):
            word_count = len(re.findall(r'[a-zA-Z]{3,}', line))
            if word_count <= 2:
                is_noise = True

        if not is_noise:
            cleaned_lines.append(line)

    # Join lines back together
    text = ' '.join(cleaned_lines)

    # Clean up extra whitespace
    text = re.sub(r' +', ' ', text)
    text = re.sub(r'\n+', '\n', text)

    # Remove leftover page markers inline
    text = re.sub(r'Page No\.\s*[ivxlcdm\d]+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'CCET IPS', '', text, flags=re.IGNORECASE)
    text = re.sub(r'AskDocs AI\s+AskDocs AI', 'AskDocs AI', text)

    # Final strip
    text = text.strip()

    return text