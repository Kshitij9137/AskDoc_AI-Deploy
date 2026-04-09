import re


def split_into_chunks(text, chunk_size=400, overlap=50):
    """
    Improved chunking strategy:
    1. First split text into paragraphs
    2. Then combine paragraphs into chunks
    3. Respect sentence boundaries
    4. Skip chunks that are too short or just noise
    """
    # Step 1: Split into paragraphs
    paragraphs = split_into_paragraphs(text)

    # Step 2: Combine paragraphs into chunks
    chunks = combine_paragraphs_into_chunks(
        paragraphs,
        chunk_size=chunk_size,
        overlap=overlap
    )

    return chunks


def split_into_paragraphs(text):
    """
    Split text into meaningful paragraphs.
    A paragraph is a group of related sentences.
    """
    # Split on double newlines or sentence endings
    # followed by what looks like a new topic
    raw_paragraphs = re.split(r'\n{2,}|(?<=[.!?])\s{2,}', text)

    paragraphs = []
    for para in raw_paragraphs:
        para = para.strip()

        # Skip empty or very short paragraphs
        if not para or len(para.split()) < 5:
            continue

        # Skip paragraphs that are just noise
        if is_noise_paragraph(para):
            continue

        paragraphs.append(para)

    return paragraphs


def is_noise_paragraph(text):
    """
    Returns True if paragraph is noise and should be skipped.
    """
    text_lower = text.lower().strip()

    noise_patterns = [
        r'^page\s+no',
        r'^ccet\s+ips',
        r'^askdocs\s+ai\s*$',
        r'^\d+\s*$',
        r'^[ivxlcdm]+\s*$',
        r'^table\s+of\s+content',
        r'^sr\.?\s*no',
        r'^submitted\s+by',
        r'^batch\s+year',
        r'^enrolment\s+no',
        r'^project\s+guide',
    ]

    for pattern in noise_patterns:
        if re.match(pattern, text_lower):
            return True

    # Skip if less than 5 meaningful words
    words = re.findall(r'[a-zA-Z]{3,}', text)
    if len(words) < 5:
        return True

    return False


def combine_paragraphs_into_chunks(paragraphs, chunk_size=400, overlap=50):
    """
    Combine paragraphs into chunks of approximately chunk_size words.
    Tries to keep related paragraphs together.
    """
    chunks = []
    current_words = []
    current_count = 0

    for para in paragraphs:
        para_words = para.split()
        para_count = len(para_words)

        # If a single paragraph is longer than chunk_size
        # split it into sentences first
        if para_count > chunk_size:
            # Save current chunk first
            if current_words and current_count >= 50:
                chunks.append(' '.join(current_words))
                # Keep overlap
                current_words = current_words[-overlap:]
                current_count = len(current_words)

            # Split long paragraph into sentence chunks
            sentence_chunks = split_long_paragraph(
                para, chunk_size, overlap
            )
            chunks.extend(sentence_chunks)
            continue

        # If adding this paragraph exceeds chunk size
        if current_count + para_count > chunk_size and current_count >= 50:
            # Save current chunk
            chunks.append(' '.join(current_words))

            # Start new chunk with overlap from previous
            overlap_words = current_words[-overlap:] if overlap else []
            current_words = overlap_words + para_words
            current_count = len(current_words)

        else:
            # Add paragraph to current chunk
            current_words.extend(para_words)
            current_count += para_count

    # Don't forget the last chunk
    if current_words and current_count >= 30:
        chunks.append(' '.join(current_words))

    # Final filter — remove chunks that are too short
    # or contain mostly noise
    chunks = [
        c for c in chunks
        if len(c.split()) >= 30
        and not is_noise_paragraph(c)
    ]

    return chunks


def split_long_paragraph(text, chunk_size=400, overlap=50):
    """
    Split a long paragraph into chunks at sentence boundaries.
    """
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', text)

    chunks = []
    current_words = []
    current_count = 0

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        s_words = sentence.split()
        s_count = len(s_words)

        if current_count + s_count > chunk_size and current_count >= 30:
            if current_words:
                chunks.append(' '.join(current_words))
            overlap_words = current_words[-overlap:] if overlap else []
            current_words = overlap_words + s_words
            current_count = len(current_words)
        else:
            current_words.extend(s_words)
            current_count += s_count

    if current_words and current_count >= 20:
        chunks.append(' '.join(current_words))

    return chunks