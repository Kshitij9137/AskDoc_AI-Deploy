import pdfplumber
import re


def extract_text_from_pdf(file_path):
    """
    Extract text from each page of a PDF file.
    Returns a list of dictionaries with page number and text.
    
    Example output:
    [
        {"page_number": 1, "text": "This is page one content..."},
        {"page_number": 2, "text": "This is page two content..."},
    ]
    """
    pages_data = []

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            raw_text = page.extract_text()

            if raw_text:  # skip empty pages
                cleaned = clean_text(raw_text)
                if cleaned:
                    pages_data.append({
                        'page_number': page_num,
                        'text': cleaned
                    })

    return pages_data


def clean_text(text):
    """
    Clean raw extracted text.
    - Remove extra whitespace
    - Remove extra blank lines
    - Strip leading/trailing spaces
    """
    # Replace multiple spaces with single space
    text = re.sub(r' +', ' ', text)

    # Replace multiple newlines with single newline
    text = re.sub(r'\n+', '\n', text)

    # Remove lines that are just spaces or special chars
    lines = text.split('\n')
    cleaned_lines = [
        line.strip() for line in lines
        if line.strip() and len(line.strip()) > 2
    ]

    return '\n'.join(cleaned_lines)