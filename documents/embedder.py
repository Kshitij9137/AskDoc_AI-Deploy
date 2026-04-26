import json
import os
from .models import DocumentChunk, ChunkEmbedding

_model = None

def get_model():
    global _model
    if _model is None:
        print("Loading SentenceTransformer model...")
        from sentence_transformers import SentenceTransformer  # import here, not at top
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully!")
    return _model


def generate_embeddings_for_document(document_id):
    chunks = list(DocumentChunk.objects.filter(document_id=document_id))

    if not chunks:
        print(f"No chunks found for document {document_id}")
        return False

    print(f"Generating embeddings for {len(chunks)} chunks...")
    model = get_model()

    # Encode ALL chunks in one batch — much faster and lower peak memory
    texts = [chunk.text for chunk in chunks]
    vectors = model.encode(texts, batch_size=8, show_progress_bar=False)

    for chunk, vector in zip(chunks, vectors):
        vector_json = json.dumps(vector.tolist())
        ChunkEmbedding.objects.update_or_create(
            chunk=chunk,
            defaults={'embedding_vector': vector_json}
        )

    print(f"Embeddings generated for document {document_id} ✅")
    return True


def get_question_embedding(question_text):
    return get_model().encode(question_text)