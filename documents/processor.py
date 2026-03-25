from .models import Document, ExtractedText, DocumentChunk
from .extractor import extract_text_from_pdf
from .chunker import split_into_chunks


def process_document(document_id):
    """
    Full document processing pipeline:
    Step 1 — Extract text from PDF page by page
    Step 2 — Save extracted text to ExtractedText model
    Step 3 — Combine ALL pages then chunk together
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

    # ── STEP 3 & 4: Combine all text then chunk ────────────
    # Combine all pages into one big text first
    full_text = '\n'.join([page['text'] for page in pages_data])

    # Use smaller chunk size so short documents also get chunked
    chunks = split_into_chunks(
        full_text,
        chunk_size=150,   # reduced from 400 to 150 words
        overlap=20        # reduced overlap accordingly
    )

    chunk_index = 0
    for chunk_text in chunks:
        # Skip very short chunks
        if len(chunk_text.split()) < 10:
            continue

        # Figure out which page this chunk belongs to
        # (use page 1 as default for combined text)
        DocumentChunk.objects.create(
            document=document,
            chunk_index=chunk_index,
            text=chunk_text,
            page_number=1
        )
        chunk_index += 1

    print(f"Created {chunk_index} chunks for: {document.title}")

    # ── STEP 5: Mark as processed ──────────────────────────
    document.is_processed = True
    document.save()

    return True