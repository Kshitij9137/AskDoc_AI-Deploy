from .models import Document, ExtractedText, DocumentChunk
from .extractor import extract_text_from_pdf
from .chunker import split_into_chunks


def process_document(document_id):
    """
    Full document processing pipeline:
    Step 1 — Extract text from PDF
    Step 2 — Save extracted text
    Step 3 — Chunk text
    Step 4 — Save chunks
    Step 5 — Generate embeddings
    Step 6 — Build FAISS index
    Step 7 — Mark as processed
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

    ExtractedText.objects.filter(document=document).delete()
    DocumentChunk.objects.filter(document=document).delete()

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
        chunks = split_into_chunks(
            page['text'],
            chunk_size=400,
            overlap=50
        )

        for chunk_text in chunks:
            if len(chunk_text.split()) < 20:
                continue

            DocumentChunk.objects.create(
                document=document,
                chunk_index=chunk_index,
                text=chunk_text,
                page_number=page['page_number']
            )
            chunk_index += 1

    print(f"Created {chunk_index} chunks.")

    # ── STEP 5: Generate embeddings ────────────────────────
    from .embedder import generate_embeddings_for_document
    generate_embeddings_for_document(document_id)

    # ── STEP 6: Build FAISS index ──────────────────────────
    from .faiss_store import build_faiss_index
    build_faiss_index()

    # ── STEP 7: Mark as processed ──────────────────────────
    document.is_processed = True
    document.save()

    return True