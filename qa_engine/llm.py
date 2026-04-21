import os
import re
import requests

# ── Groq Configuration ─────────────────────────
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
GROQ_MODEL = "llama-3.1-8b-instant" 
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# Noise phrases to clean before sending to model
NOISE_PHRASES = [
    r'Page No\.\s*\S+',
    r'CCET\s+IPS',
    r'\bccet\b',
    r'[◦▪•●▸▹►◆▷]',
]


def clean_context(text):
    """
    Clean context before sending to Groq.
    Remove PDF artifacts and special characters.
    """
    for pattern in NOISE_PHRASES:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    # Remove API paths
    text = re.sub(r'(POST|GET|PUT|DELETE)\s+/api/\S+', '', text)

    # Clean lines
    lines = text.split('\n')
    clean = []
    for line in lines:
        line = line.strip()
        if not line or len(line.split()) < 4:
            continue
        clean.append(line)

    text = ' '.join(clean)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def generate_answer_with_model(question, context):
    """
    Use Groq's Llama 3 API to generate a fluent,
    accurate answer from the provided context.

    This replaces Flan-T5 completely.
    Same function signature — pipeline.py unchanged.

    Advantages over Flan-T5:
    - No RAM usage (just API call)
    - 10x better answer quality
    - Response in <1 second
    - Handles summarization, listing, conclusions
    """

    # Check API key exists
    if not GROQ_API_KEY:
        print("⚠️ No GROQ_API_KEY in .env — using extractive fallback")
        return None

    if not context or not question:
        return None

    # Clean the context
    context = clean_context(context)

    # Trim to fit token limits (Groq allows 8192 tokens)
    # ~600 words is safe with prompt overhead
    words = context.split()
    if len(words) > 600:
        context = ' '.join(words[:600])

    # Build the prompt
    system_prompt = """You are a helpful document assistant for AskDocs AI.
Your job is to answer questions based ONLY on the provided context.

Rules:
- Answer based strictly on the context provided
- Be concise and clear (2-4 sentences for most questions)
- For summarization, give a brief paragraph
- For lists/milestones, use numbered format
- If the answer is not in the context, say: "The document does not contain information about this."
- Do not make up information
- Do not mention "the context" or "the document" in your answer"""

    user_message = f"""Context from documents:
{context}

Question: {question}

Answer:"""

    try:
        print(f"Asking Groq ({GROQ_MODEL})...")

        response = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message}
                ],
                "temperature": 0.3,
                "max_tokens": 300,
                "top_p": 0.9,
            },
            timeout=20
        )

        # Handle response
        if response.status_code == 200:
            data = response.json()
            answer = data["choices"][0]["message"]["content"].strip()
            print(f"✅ Groq answered: {answer[:120]}")

            # Reject refusal answers
            BAD_RESPONSES = [
                'does not contain information',
                'not provided in the context',
                'context does not',
                'no information available',
                'cannot answer',
                'not mentioned',
                'i don\'t know',
                'not found in',
            ]

            answer_lower = answer.lower()
            if any(bad in answer_lower for bad in BAD_RESPONSES):
                print("Groq said not found — using extractive fallback")
                return None

            # Reject too-short answers
            if len(answer.split()) < 4:
                print("Groq answer too short — using extractive fallback")
                return None

            return answer

        elif response.status_code == 429:
            print("⚠️ Groq rate limit hit — using extractive fallback")
            return None

        elif response.status_code == 401:
            print("❌ Groq API key invalid — check your .env file")
            return None

        else:
            print(f"❌ Groq API error {response.status_code}: {response.text[:200]}")
            return None

    except requests.exceptions.Timeout:
        print("⚠️ Groq API timeout (20s) — using extractive fallback")
        return None

    except requests.exceptions.ConnectionError:
        print("⚠️ No internet connection — using extractive fallback")
        return None

    except Exception as e:
        print(f"❌ Groq unexpected error: {e}")
        return None