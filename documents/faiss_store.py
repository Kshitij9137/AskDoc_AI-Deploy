import json
import os
import numpy as np
import faiss

# Paths where FAISS index and mapping will be saved
FAISS_INDEX_PATH = "faiss_index/index.faiss"
CHUNK_MAP_PATH = "faiss_index/chunk_map.json"

# Embedding size for all-MiniLM-L6-v2 model
EMBEDDING_DIM = 384


def build_faiss_index():
    """
    Build FAISS index from all saved embeddings.

    Steps:
    1. Load all ChunkEmbedding objects from DB
    2. Convert vectors to numpy array
    3. Build FAISS index
    4. Save index to disk
    5. Save chunk_id mapping to disk
    """
    from .models import ChunkEmbedding

    embeddings = ChunkEmbedding.objects.select_related('chunk').all()

    if not embeddings.exists():
        print("No embeddings found. Upload and process a document first.")
        return False

    vectors = []
    chunk_map = {}  # maps FAISS position → chunk ID

    for i, emb in enumerate(embeddings):
        vector = json.loads(emb.embedding_vector)
        vectors.append(vector)
        chunk_map[str(i)] = emb.chunk.id

    # Convert to numpy float32 array (required by FAISS)
    vectors_np = np.array(vectors, dtype=np.float32)

    # Create FAISS index (L2 = Euclidean distance)
    index = faiss.IndexFlatL2(EMBEDDING_DIM)
    index.add(vectors_np)

    # Save index to disk
    os.makedirs("faiss_index", exist_ok=True)
    faiss.write_index(index, FAISS_INDEX_PATH)

    # Save chunk mapping to disk
    with open(CHUNK_MAP_PATH, 'w') as f:
        json.dump(chunk_map, f)

    print(f"FAISS index built with {index.ntotal} vectors ✅")
    return True


def load_faiss_index():
    """
    Load FAISS index and chunk mapping from disk.
    Returns (index, chunk_map) or (None, None) if not found.
    """
    if not os.path.exists(FAISS_INDEX_PATH):
        print("FAISS index not found. Run build_faiss_index() first.")
        return None, None

    index = faiss.read_index(FAISS_INDEX_PATH)

    with open(CHUNK_MAP_PATH, 'r') as f:
        chunk_map = json.load(f)

    print(f"FAISS index loaded with {index.ntotal} vectors ✅")
    return index, chunk_map


def search_faiss(question_vector, top_k=5):
    """
    Search FAISS index for most similar chunks.

    Returns list of chunk IDs ranked by similarity.
    """
    index, chunk_map = load_faiss_index()

    if index is None:
        return []

    # Convert to numpy float32
    query = np.array([question_vector], dtype=np.float32)

    # Search — returns distances and indices
    distances, indices = index.search(query, top_k)

    # Map FAISS indices back to chunk IDs
    chunk_ids = []
    for idx in indices[0]:
        if idx == -1:
            continue
        chunk_id = chunk_map.get(str(idx))
        if chunk_id:
            chunk_ids.append(chunk_id)

    return chunk_ids