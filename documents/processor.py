from .models import Document, ExtractedText, DocumentChunk
from .extractor import extract_text_from_pdf
from .chunker import split_into_chunks


def process_document(document_id):
    """
    Full document processing pipeline:
    Step 1 — Extract text from PDF page by page
    Step 2 — Save extracted text to ExtractedText model
    Step 3 — Chunk all text into 300-500 word pieces
    Step 4 — Save chunks to DocumentChunk model
    Step 5 — Mark document as processed
    """
    try:
        document = Document.objects.get(id=document_id)
    except Document.DoesNotExist:
        print(f"Document {document_id} not found.")
        return False

    file_path = document.file.path
    print(f"Processing: {document.title}")

    # ── STEP 1 & 2: Extract and save text ──────────────────
    pages_data = extract_text_from_pdf(file_path)

    if not pages_data:
        print(f"No text extracted from: {document.title}")
        return False

    # Clear old data if reprocessing
    ExtractedText.objects.filter(document=document).delete()
    DocumentChunk.objects.filter(document=document).delete()

    # Save extracted text page by page
    for page in pages_data:
        ExtractedText.objects.create(
            document=document,
            page_number=page['page_number'],
            raw_text=page['text']
        )

    print(f"Extracted {len(pages_data)} pages.")

    # ── STEP 3 & 4: Chunk and save ─────────────────────────
    chunk_index = 0

    for page in pages_data:
        page_text = page['text']
        page_number = page['page_number']

        # Split this page's text into chunks
        chunks = split_into_chunks(
            page_text,
            chunk_size=400,
            overlap=50
        )

        for chunk_text in chunks:
            # Skip very short chunks (less than 20 words)
            if len(chunk_text.split()) < 20:
                continue

            DocumentChunk.objects.create(
                document=document,
                chunk_index=chunk_index,
                text=chunk_text,
                page_number=page_number
            )
            chunk_index += 1

    print(f"Created {chunk_index} chunks for: {document.title}")

    # ── STEP 5: Mark as processed ──────────────────────────
    document.is_processed = True
    document.save()

    return True