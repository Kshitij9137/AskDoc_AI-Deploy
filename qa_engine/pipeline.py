import re
from .searcher import search_similar_chunks


# ── Noise filters ──────────────────────────────
NOISE_PHRASES = [
    'page no', 'ccet ips', 'ccet', 'table of content',
    'sr. no', 'submitted by', 'batch year', 'enrolment no',
    'project guide', 'university of allahabad',
    'institute of professional', 'centre of computer',
    'prayagraj', 'uttar pradesh', 'master of computer',
    '4th semester', '2024-2026',
]

STOP_WORDS = {
    'what', 'is', 'the', 'a', 'an', 'of', 'in', 'to',
    'and', 'or', 'for', 'how', 'why', 'who', 'when',
    'where', 'are', 'was', 'were', 'does', 'do', 'did',
    'can', 'could', 'would', 'should', 'tell', 'me',
    'about', 'explain', 'describe', 'list', 'give',
    'define', 'definition', 'please', 'this', 'that',
    'these', 'those', 'with', 'from', 'has', 'have',
    'been', 'will', 'its', 'their', 'which', 'some',
}


def is_noise_sentence(sentence):
    """
    Returns True if sentence is noise and
    should NOT appear in the answer.
    """
    sentence_lower = sentence.lower()

    # Check noise phrases
    for phrase in NOISE_PHRASES:
        if phrase in sentence_lower:
            return True

    # Skip sentences with too many numbers
    digits = re.findall(r'\d', sentence)
    if len(digits) > len(sentence) * 0.3:
        return True

    # Skip sentences that look like headers
    # (ALL CAPS or Title Case with few words)
    words = sentence.split()
    if len(words) < 8:
        caps_words = sum(1 for w in words if w.isupper() and len(w) > 1)
        if caps_words >= len(words) * 0.5:
            return True

    return False


def get_question_keywords(question):
    """
    Extract meaningful keywords from question.
    Removes stop words and short words.
    """
    words = re.findall(r'[a-zA-Z]+', question.lower())
    keywords = set(
        w for w in words
        if w not in STOP_WORDS and len(w) > 2
    )
    return keywords


def score_sentence(sentence, keywords):
    """
    Score a sentence based on how relevant it is
    to the question keywords.

    Scoring rules:
    +2 per exact keyword match
    +1 if sentence is longer (more informative)
    +1 if sentence starts with a keyword
    -1 if sentence is very short
    """
    sentence_lower = sentence.lower()
    sentence_words = set(re.findall(r'[a-zA-Z]+', sentence_lower))
    word_list = sentence.split()

    score = 0

    # Exact keyword matches
    matches = keywords & sentence_words
    score += len(matches) * 2

    # Partial matches (keyword appears as substring)
    for keyword in keywords:
        if keyword in sentence_lower and keyword not in sentence_words:
            score += 1

    # Bonus for longer informative sentences
    if len(word_list) > 20:
        score += 1
    if len(word_list) > 40:
        score += 1

    # Bonus if sentence starts with a keyword
    if word_list and word_list[0].lower() in keywords:
        score += 1

    # Penalty for very short sentences
    if len(word_list) < 8:
        score -= 2

    return score


def build_context(chunks, max_words=800):
    """
    Combine retrieved chunks into a single context string.
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
    Extract the most relevant answer sentences from context.

    Strategy:
    1. Split context into sentences
    2. Filter out noise sentences
    3. Score each sentence by keyword relevance
    4. Return top 3 highest scoring sentences
    """
    if not context:
        return "I could not find relevant information to answer your question."

    # Get question keywords
    keywords = get_question_keywords(question)

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', context)

    scored = []
    for sentence in sentences:
        sentence = sentence.strip()

        # Skip empty or very short sentences
        if len(sentence.split()) < 6:
            continue

        # Skip noise sentences
        if is_noise_sentence(sentence):
            continue

        # Score the sentence
        score = score_sentence(sentence, keywords)

        # Only include sentences with positive score
        if score > 0:
            scored.append((score, sentence))

    # Sort by score highest first
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        # For summary questions return multiple clean sentences
        clean_sentences = []
        for sentence in sentences:
            sentence = sentence.strip()
            if (len(sentence.split()) >= 10
                    and not is_noise_sentence(sentence)
                    and '/api/' not in sentence
                    and sentence.count('◦') + sentence.count('•') < 2):
                clean_sentences.append(sentence)
            if len(clean_sentences) >= 3:
                break

        if clean_sentences:
            return ' '.join(clean_sentences)
        return "I found related content but could not extract a clear answer. Please try rephrasing your question."

    # For summary/list questions return top 5 sentences
    question_lower = question.lower()
    is_summary = any(t in question_lower for t in [
        'conclude', 'summarize', 'list', 'milestones',
        'overview', 'all', 'timeline', 'steps', 'references'
    ])

    top_count = 5 if is_summary else 3
    top_sentences = [s for _, s in scored[:top_count]]

    # Restore original order
    original_order = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence in top_sentences:
            original_order.append(sentence)
            if len(original_order) == len(top_sentences):
                break

    answer = ' '.join(original_order) if original_order else ' '.join(top_sentences)
    return answer

    # Take top 3 sentences
    top_sentences = [s for _, s in scored[:3]]

    # Sort them back in original order for readability
    original_order = []
    for sentence in sentences:
        sentence = sentence.strip()
        if sentence in top_sentences:
            original_order.append(sentence)
            if len(original_order) == len(top_sentences):
                break

    answer = ' '.join(original_order) if original_order else ' '.join(top_sentences)
    return answer


def build_sources(chunks):
    """
    Build a clean deduplicated list of sources.
    """
    seen = set()
    sources_data = []
    chunks_for_db = []

    for chunk in chunks:
        key = (chunk['document_title'], chunk['page_number'])

        if key not in seen:
            seen.add(key)
            sources_data.append({
                'document': chunk['document_title'],
                'document_id': chunk['document_id'],
                'page': chunk['page_number']
            })

        chunks_for_db.append(chunk)

    return sources_data, chunks_for_db


def save_query_to_db(user, question, answer, chunks):
    """
    Save the question, answer, and sources to database.
    """
    from .models import QueryLog, QuerySource
    from documents.models import Document

    query_log = QueryLog.objects.create(
        user=user,
        question=question,
        answer=answer
    )

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
    Full RAG pipeline with Flan-T5 generative model:
    1. Semantic search via FAISS
    2. Filter noisy chunks
    3. Build context
    4. Generate answer with Flan-T5
    5. Fall back to extractive if model fails
    6. Return structured response
    """
    if not question or not question.strip():
        return {
            "question": question,
            "answer": "Please provide a valid question.",
            "sources": [],
        }

    print(f"\nProcessing: {question}")

    # Step 1: Semantic search — retrieve more chunks
    chunks = search_similar_chunks(question, top_k=10)

    if not chunks:
        return {
            "question": question,
            "answer": "No relevant documents found. Please upload documents first.",
            "sources": [],
        }

    # Step 2: Filter noisy chunks
    import re as _re
    def is_usable(text):
        if len(text.split()) < 25:
            return False
        if 'table of content' in text.lower():
            return False
        if _re.search(r'\.{2,}\s*\d+', text):
            return False
        bullet_count = text.count('◦') + text.count('•') + text.count('▪')
        if bullet_count > 5:
            return False
        return True

    usable_chunks = [c for c in chunks if is_usable(c['text'])]

    # Fall back to all chunks if filtering removes too many
    if len(usable_chunks) < 2:
        usable_chunks = chunks

    # Step 3: Build context from best chunks
    context = build_context(usable_chunks, max_words=500)

    # Step 4: Build sources
    sources_data, chunks_for_db = build_sources(usable_chunks)

    # Step 5: Try Flan-T5 generative model
    print("Running Flan-T5...")
    from .llm import generate_answer_with_model
    answer = generate_answer_with_model(question, context)

    if answer:
        print(f"✅ Flan-T5 answered!")
    else:
        # Step 6: Fall back to improved extractive
        print("⚠️ Flan-T5 fallback to extractive...")
        answer = extract_answer(question, context)

    # Step 7: Save to DB
    if user:
        save_query_to_db(user, question, answer, chunks_for_db)

    return {
        "question": question,
        "answer": answer,
        "sources": sources_data,
    }