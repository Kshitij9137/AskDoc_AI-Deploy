import re


def split_into_chunks(text, chunk_size=400, overlap=50):
    """
    Split text into chunks, respecting sentence boundaries.

    Instead of blindly splitting by word count,
    this version tries to end chunks at sentence boundaries
    so context is preserved better.
    """
    # First split into sentences
    sentences = split_into_sentences(text)

    chunks = []
    current_chunk_words = []
    current_word_count = 0

    for sentence in sentences:
        sentence_words = sentence.split()
        sentence_word_count = len(sentence_words)

        # If adding this sentence exceeds chunk size
        # and we already have enough words, save the chunk
        if (current_word_count + sentence_word_count > chunk_size
                and current_word_count >= 50):

            chunk_text = ' '.join(current_chunk_words)
            chunks.append(chunk_text)

            # Keep last few words for overlap
            overlap_words = current_chunk_words[-overlap:] if overlap else []
            current_chunk_words = overlap_words + sentence_words
            current_word_count = len(current_chunk_words)

        else:
            current_chunk_words.extend(sentence_words)
            current_word_count += sentence_word_count

    # Add the last remaining chunk
    if current_chunk_words:
        chunk_text = ' '.join(current_chunk_words)
        chunks.append(chunk_text)

    return chunks


def split_into_sentences(text):
    """
    Split text into sentences using punctuation.
    Handles abbreviations and edge cases.
    """
    # Split on period, exclamation, question mark
    # followed by space and capital letter
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

    # Further split on newlines if sentences are very long
    result = []
    for sentence in sentences:
        if len(sentence.split()) > 150:
            # Split long sentences at newlines or semicolons
            parts = re.split(r'[;\n]', sentence)
            result.extend([p.strip() for p in parts if p.strip()])
        else:
            if sentence.strip():
                result.append(sentence.strip())

    return result