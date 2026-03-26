import json
from sentence_transformers import SentenceTransformer
from .models import DocumentChunk, ChunkEmbedding

# Load model once when file is imported
# all-MiniLM-L6-v2 is fast, lightweight, and accurate
# It converts text into 384-dimensional vectors
print("Loading sentence transformer model...")
model = SentenceTransformer('all-MiniLM-L6-v2')
print("Model loaded successfully!")


def generate_embeddings_for_document(document_id):
    """
    Generate and save embeddings for all chunks
    of a given document.

    Steps:
    1. Get all chunks for the document
    2. Convert each chunk text into a vector
    3. Save vector to ChunkEmbedding model
    """
    chunks = DocumentChunk.objects.filter(
        document_id=document_id
    )

    if not chunks.exists():
        print(f"No chunks found for document {document_id}")
        return False

    print(f"Generating embeddings for {chunks.count()} chunks...")

    for chunk in chunks:
        # Convert text to vector (list of 384 floats)
        vector = model.encode(chunk.text)

        # Convert numpy array to JSON string for storage
        vector_json = json.dumps(vector.tolist())

        # Save or update embedding
        ChunkEmbedding.objects.update_or_create(
            chunk=chunk,
            defaults={'embedding_vector': vector_json}
        )

    print(f"Embeddings generated for document {document_id} ✅")
    return True


def get_question_embedding(question_text):
    """
    Convert a user's question into a vector embedding.
    Used later in Phase 4C for similarity search.
    """
    vector = model.encode(question_text)
    return vector