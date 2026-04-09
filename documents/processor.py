from .models import Document, ExtractedText, DocumentChunk
from .extractor import extract_text_from_pdf
from .chunker import split_into_chunks


def process_document(document_id):
    """
    Full document processing pipeline:
    Step 1 — Extract & clean text from PDF
    Step 2 — Save extracted text to DB
    Step 3 — Chunk text intelligently
    Step 4 — Save chunks to DB
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
    print(f"\n{'='*50}")
    print(f"Processing: {document.title}")
    print(f"{'='*50}")

    # ── STEP 1 & 2: Extract and save text ──────────
    pages_data = extract_text_from_pdf(file_path)

    if not pages_data:
        print(f"❌ No text extracted from: {document.title}")
        return False

    # Clear old data
    ExtractedText.objects.filter(document=document).delete()
    DocumentChunk.objects.filter(document=document).delete()

    # Save extracted text
    total_words = 0
    for page in pages_data:
        ExtractedText.objects.create(
            document=document,
            page_number=page['page_number'],
            raw_text=page['text']
        )
        total_words += len(page['text'].split())

    print(f"✅ Extracted {len(pages_data)} pages ({total_words} words)")

    # ── STEP 3 & 4: Chunk and save ─────────────────
    chunk_index = 0

    for page in pages_data:
        chunks = split_into_chunks(
            page['text'],
            chunk_size=400,
            overlap=50
        )

        for chunk_text in chunks:
            # Skip very short chunks
            if len(chunk_text.split()) < 30:
                continue

            DocumentChunk.objects.create(
                document=document,
                chunk_index=chunk_index,
                text=chunk_text,
                page_number=page['page_number']
            )
            chunk_index += 1

    print(f"✅ Created {chunk_index} chunks")

    if chunk_index == 0:
        print("❌ No chunks created — document may be empty or all noise")
        return False

    # ── STEP 5: Generate embeddings ────────────────
    print("⏳ Generating embeddings...")
    from .embedder import generate_embeddings_for_document
    generate_embeddings_for_document(document_id)
    print("✅ Embeddings generated")

    # ── STEP 6: Build FAISS index ──────────────────
    print("⏳ Building FAISS index...")
    from .faiss_store import build_faiss_index
    build_faiss_index()
    print("✅ FAISS index built")

    # ── STEP 7: Mark as processed ──────────────────
    document.is_processed = True
    document.save()

    print(f"\n✅ Document '{document.title}' fully processed!")
    return True