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
    Scores each sentence by how many question
    keywords it contains.
    """
    if not context:
        return "I could not find relevant information to answer your question."

    import re
    sentences = re.split(r'(?<=[.!?])\s+', context)

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

    scored = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 20:
            continue
        sentence_words = set(sentence.lower().split())
        score = len(question_words & sentence_words)
        scored.append((score, sentence))

    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return context[:500]

    top_sentences = [s for _, s in scored[:3]]
    return ' '.join(top_sentences)


def build_sources(chunks):
    """
    Build a clean deduplicated list of sources
    from retrieved chunks.

    Returns:
    - sources_data: list of dicts for JSON response
    - chunks_for_db: list of chunks to save to DB
    """
    seen = set()
    sources_data = []
    chunks_for_db = []

    for chunk in chunks:
        key = (chunk['document_title'], chunk['page_number'])

        # Add to JSON response (deduplicated)
        if key not in seen:
            seen.add(key)
            sources_data.append({
                'document': chunk['document_title'],
                'document_id': chunk['document_id'],
                'page': chunk['page_number']
            })

        # Keep all chunks for DB saving
        chunks_for_db.append(chunk)

    return sources_data, chunks_for_db


def save_query_to_db(user, question, answer, chunks):
    """
    Save the question, answer, and sources to database.
    This enables chat history and analytics.
    """
    from .models import QueryLog, QuerySource
    from documents.models import Document

    # Save the query log
    query_log = QueryLog.objects.create(
        user=user,
        question=question,
        answer=answer
    )

    # Save each source reference
    seen = set()
    for chunk in chunks:
        key = (chunk['document_id'], chunk['page_number'])
        if key in seen:
            continue
        seen.add(key)

        try:
            document = Document.objects.get(id=chunk['document_id'])
            QuerySource.objects.create(
                query=query_log,
                document=document,
                page_number=chunk['page_number'],
                relevant_text=chunk['text'][:500]
            )
        except Document.DoesNotExist:
            continue

    return query_log


def answer_question(question, user=None):
    """
    Main Q&A pipeline:
    1. Search for relevant chunks
    2. Build context from chunks
    3. Extract answer from context
    4. Build sources list
    5. Save to database (if user provided)
    6. Return structured response
    """
    if not question or not question.strip():
        return {
            "question": question,
            "answer": "Please provide a valid question.",
            "sources": [],
        }

    print(f"Processing question: {question}")

    # Step 1: Semantic search
    chunks = search_similar_chunks(question, top_k=5)

    if not chunks:
        return {
            "question": question,
            "answer": "No relevant documents found. Please upload documents first.",
            "sources": [],
        }

    # Step 2: Build context
    context = build_context(chunks, max_words=800)

    # Step 3: Extract answer
    answer = extract_answer(question, context)

    # Step 4: Build sources
    sources_data, chunks_for_db = build_sources(chunks)

    # Step 5: Save to DB if user is provided
    if user:
        save_query_to_db(user, question, answer, chunks_for_db)

    # Step 6: Return structured response
    return {
        "question": question,
        "answer": answer,
        "sources": sources_data,
    }