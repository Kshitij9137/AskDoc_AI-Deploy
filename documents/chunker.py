def split_into_chunks(text, chunk_size=400, overlap=50):
    """
    Split text into chunks of approximately chunk_size words.
    overlap = how many words to repeat from previous chunk
    to preserve context at boundaries.

    Example:
    chunk_size = 400 words
    overlap    = 50 words

    Chunk 1: words 1   → 400
    Chunk 2: words 350 → 750  (50 word overlap)
    Chunk 3: words 700 → 1100 (50 word overlap)
    """
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk_words = words[start:end]
        chunk_text = ' '.join(chunk_words)
        chunks.append(chunk_text)

        # Move forward by chunk_size minus overlap
        start += chunk_size - overlap

    return chunks