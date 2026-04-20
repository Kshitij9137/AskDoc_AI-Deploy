import re
from .searcher import search_similar_chunks
from sentence_transformers import CrossEncoder

# ── Load cross-encoder for reranking ─────────────
print("Loading cross-encoder for reranking...")
reranker = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
print("Cross-encoder loaded! ✅")

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
    sentence_lower = sentence.lower()
    for phrase in NOISE_PHRASES:
        if phrase in sentence_lower:
            return True
    digits = re.findall(r'\d', sentence)
    if len(digits) > len(sentence) * 0.3:
        return True
    words = sentence.split()
    if len(words) < 8:
        caps_words = sum(1 for w in words if w.isupper() and len(w) > 1)
        if caps_words >= len(words) * 0.5:
            return True
    return False


def get_question_keywords(question):
    words = re.findall(r'[a-zA-Z]+', question.lower())
    keywords = set(w for w in words if w not in STOP_WORDS and len(w) > 2)
    return keywords


def score_sentence(sentence, keywords):
    sentence_lower = sentence.lower()
    sentence_words = set(re.findall(r'[a-zA-Z]+', sentence_lower))
    word_list = sentence.split()
    score = 0
    matches = keywords & sentence_words
    score += len(matches) * 2
    for keyword in keywords:
        if keyword in sentence_lower and keyword not in sentence_words:
            score += 1
    if len(word_list) > 20:
        score += 1
    if len(word_list) > 40:
        score += 1
    if word_list and word_list[0].lower() in keywords:
        score += 1
    if len(word_list) < 8:
        score -= 2
    return score


def build_context(chunks, max_words=600):
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
    if not context:
        return "I could not find relevant information to answer your question."
    keywords = get_question_keywords(question)
    sentences = re.split(r'(?<=[.!?])\s+', context)
    scored = []
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence.split()) < 6:
            continue
        if is_noise_sentence(sentence):
            continue
        score = score_sentence(sentence, keywords)
        if score > 0:
            scored.append((score, sentence))
    scored.sort(key=lambda x: x[0], reverse=True)
    if not scored:
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
        return "I found related content but could not extract a clear answer."
    question_lower = question.lower()
    is_summary = any(t in question_lower for t in [
        'conclude', 'summarize', 'list', 'milestones',
        'overview', 'all', 'timeline', 'steps', 'references'
    ])
    top_count = 5 if is_summary else 3
    top_sentences = [s for _, s in scored[:top_count]]
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
    from .models import QueryLog, QuerySource
    from documents.models import Document
    query_log = QueryLog.objects.create(user=user, question=question, answer=answer)
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


def is_usable_chunk(text):
    text_lower = text.lower()
    if len(text.split()) < 25:
        return False
    noise_keywords = ['table of content', 'page no.', 'ccet', 'submitted by', 'enrolment']
    if any(n in text_lower for n in noise_keywords):
        return False
    bullet_count = text.count('◦') + text.count('•') + text.count('▪')
    if bullet_count > 4:
        return False
    if text.count('.') > 30 and len(text) < 200:
        return False
    if re.match(r'^[A-Z][a-z]+\s+[A-Z][a-z]+$', text.strip()):
        return False
    return True


def rerank_chunks(question, chunks, top_k=5):
    """Re‑rank chunks using a cross‑encoder for better relevance."""
    if not chunks:
        return []
    pairs = [(question, chunk['text']) for chunk in chunks]
    scores = reranker.predict(pairs)
    # Sort by score descending
    ranked = sorted(zip(chunks, scores), key=lambda x: x[1], reverse=True)
    return [chunk for chunk, _ in ranked[:top_k]]


def answer_question(question, user=None):
    if not question or not question.strip():
        return {
            "question": question,
            "answer": "Please provide a valid question.",
            "sources": [],
        }

    print(f"\nProcessing: {question}")

    # Step 1: Retrieve top 20 chunks
    chunks = search_similar_chunks(question, top_k=30)

    if not chunks:
        return {
            "question": question,
            "answer": "No relevant documents found. Please upload documents first.",
            "sources": [],
        }

    # ✅ FILTER CHUNKS BY USER — only show results from user's own documents
    if user:
        from documents.models import Document
        user_doc_ids = set(
            Document.objects.filter(owner=user).values_list('id', flat=True)
        )
        chunks = [c for c in chunks if c['document_id'] in user_doc_ids]

    if not chunks:
        return {
            "question": question,
            "answer": "No relevant documents found in your library. Please upload your own documents first.",
            "sources": [],
        }

    # Step 2: Filter obvious noise
    usable_chunks = [c for c in chunks if is_usable_chunk(c['text'])]
    if len(usable_chunks) < 2:
        usable_chunks = chunks[:5]

    # Step 3: Rerank with cross‑encoder (top 5)
    print(f"Reranking {len(usable_chunks)} chunks...")
    best_chunks = rerank_chunks(question, usable_chunks, top_k=8)
    print(f"Selected top {len(best_chunks)} chunks after reranking.")

    # Step 4: Build context
    context = build_context(best_chunks, max_words=800)
    print(f"Context length: {len(context.split())} words")

    # Step 5: Build sources
    sources_data, chunks_for_db = build_sources(best_chunks)

    # Step 6: Generate answer with Flan‑T5
    print("Running Flan-T5...")
    from .llm import generate_answer_with_model
    answer = generate_answer_with_model(question, context)

    if answer is not None:
        print(f"✅ Flan-T5 answered: {answer[:100]}")
    else:
        print("⚠️ Flan-T5 failed, using extractive fallback...")
        answer = extract_answer(question, context)

    # Step 7: Save to DB
    if user:
        save_query_to_db(user, question, answer, chunks_for_db)


    return {
        "question": question,
        "answer": answer,
        "sources": sources_data,
    }