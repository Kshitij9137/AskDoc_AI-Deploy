from .searcher import search_similar_chunks


def build_context(chunks, max_words=800):
    """
    Combine retrieved chunks into a single context string.
    Limit total words to avoid making the answer too long.
    """
    context_parts = []
    total_words = 0

    for chunk in chunks:
        chunk_words = chunk['text'].split()
        if total_words + len(chunk_words) > max_words:
            break
        context_parts.append(chunk['text'])
        total_words += len(chunk_words)

    return '\n\n'.join(context_parts)


def extract_answer(question, context):
    """
    Extract the most relevant answer from context.

    Strategy:
    1. Split context into sentences
    2. Score each sentence by how many
       question words it contains
    3. Return top 3 most relevant sentences
       as the final answer
    """
    if not context:
        return "I could not find relevant information to answer your question."

    # Split into sentences
    import re
    sentences = re.split(r'(?<=[.!?])\s+', context)

    # Get important words from question
    # (ignore common words like 'what', 'is', 'the')
    stop_words = {
        'what', 'is', 'the', 'a', 'an', 'of', 'in',
        'to', 'and', 'or', 'for', 'how', 'why', 'who',
        'when', 'where', 'are', 'was', 'were', 'does',
        'do', 'did', 'can', 'could', 'would', 'should',
        'tell', 'me', 'about', 'explain', 'describe'
    }

    question_words = set(
        word.lower() for word in question.split()
        if word.lower() not in stop_words
    )

    # Score each sentence
    scored = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:  # skip very short sentences
            continue

        sentence_words = set(sentence.lower().split())
        # Count how many question words appear in sentence
        score = len(question_words & sentence_words)
        scored.append((score, sentence))

    # Sort by score (highest first)
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return context[:500]  # fallback: return first 500 chars

    # Return top 3 most relevant sentences joined together
    top_sentences = [s for _, s in scored[:3]]
    answer = ' '.join(top_sentences)

    return answer


def answer_question(question):
    """
    Main Q&A pipeline:
    1. Search for relevant chunks
    2. Build context from chunks
    3. Extract answer from context
    4. Return answer + sources

    Returns a dictionary:
    {
        "question": "...",
        "answer": "...",
        "sources": [...],
        "context_used": "..."
    }
    """
    if not question or not question.strip():
        return {
            "question": question,
            "answer": "Please provide a valid question.",
            "sources": [],
            "context_used": ""
        }

    print(f"Processing question: {question}")

    # Step 1: Semantic search
    chunks = search_similar_chunks(question, top_k=5)

    if not chunks:
        return {
            "question": question,
            "answer": "No relevant documents found. Please upload documents first.",
            "sources": [],
            "context_used": ""
        }

    # Step 2: Build context
    context = build_context(chunks, max_words=800)

    # Step 3: Extract answer
    answer = extract_answer(question, context)

    # Step 4: Build sources list (remove duplicates)
    seen = set()
    sources = []
    for chunk in chunks:
        key = (chunk['document_title'], chunk['page_number'])
        if key not in seen:
            seen.add(key)
            sources.append({
                'document': chunk['document_title'],
                'page': chunk['page_number']
            })

    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "context_used": context
    }