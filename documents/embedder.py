import json
import os

from sentence_transformers import SentenceTransformer
from .models import DocumentChunk, ChunkEmbedding

# Global model cache (lazy-loaded on first use)
_model = None

def get_model():
    global _model
    if _model is None:
        print("Loading SentenceTransformer model...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully!")
    return _model


def generate_embeddings_for_document(document_id):
    chunks = DocumentChunk.objects.filter(document_id=document_id)

    if not chunks.exists():
        print(f"No chunks found for document {document_id}")
        return False

    print(f"Generating embeddings for {chunks.count()} chunks...")
    model = get_model()

    for chunk in chunks:
        vector = model.encode(chunk.text)
        vector_json = json.dumps(vector.tolist())
        ChunkEmbedding.objects.update_or_create(
            chunk=chunk,
            defaults={'embedding_vector': vector_json}
        )

    print(f"Embeddings generated for document {document_id} ✅")
    return True


def get_question_embedding(question_text):
    vector = get_model().encode(question_text)
    return vector