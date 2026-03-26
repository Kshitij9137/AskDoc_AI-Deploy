from documents.faiss_store import search_faiss
from documents.embedder import get_question_embedding
from documents.models import DocumentChunk


def search_similar_chunks(question, top_k=5):
    """
    Full semantic search pipeline:
    1. Convert question to embedding
    2. Search FAISS for similar vectors
    3. Retrieve matching chunks from DB
    4. Return chunks with source info
    """

    # Step 1: Convert question to vector
    question_vector = get_question_embedding(question)

    # Step 2: Search FAISS
    chunk_ids = search_faiss(question_vector, top_k=top_k)

    if not chunk_ids:
        return []

    # Step 3: Retrieve chunks from DB
    results = []
    for chunk_id in chunk_ids:
        try:
            chunk = DocumentChunk.objects.select_related('document').get(id=chunk_id)
            results.append({
                'chunk_id': chunk.id,
                'chunk_index': chunk.chunk_index,
                'page_number': chunk.page_number,
                'text': chunk.text,
                'document_id': chunk.document.id,
                'document_title': chunk.document.title,
            })
        except DocumentChunk.DoesNotExist:
            continue

    return results


