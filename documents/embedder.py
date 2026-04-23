import json
import os
from .models import DocumentChunk, ChunkEmbedding

# Tell HuggingFace to use cached model only
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'

# Global model cache (lazy-loaded on first use)
_model = None

def _get_model():
    """Lazy-load the sentence transformer model on first use."""
    global _model
    if _model is None:
        # Import INSIDE function to delay torch loading
        from sentence_transformers import SentenceTransformer
        print("Loading sentence transformer model...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Model loaded successfully!")
    return _model


def generate_embeddings_for_document(document_id):
    """
    Generate and save embeddings for all chunks
    of a given document.
    """
    model = _get_model()
    chunks = DocumentChunk.objects.filter(
        document_id=document_id
    )

    if not chunks.exists():
        print(f"No chunks found for document {document_id}")
        return False

    print(f"Generating embeddings for {chunks.count()} chunks...")

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
    """
    Convert a user's question into a vector embedding.
    """
    model = _get_model()
    vector = model.encode(question_text)
    return vector