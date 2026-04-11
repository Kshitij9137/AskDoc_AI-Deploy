from transformers import AutoTokenizer, AutoModelForQuestionAnswering
import torch
import re

print("Loading QA model...")
MODEL_NAME = "deepset/roberta-base-squad2"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForQuestionAnswering.from_pretrained(MODEL_NAME)
print("QA model loaded! ✅")


def clean_for_model(text):
    """
    Clean text before sending to QA model.
    Remove special characters that confuse tokenizer.
    """
    # Remove bullet points and special chars
    text = re.sub(r'[◦▪•●▸▹►]', '', text)
    # Remove multiple spaces
    text = re.sub(r' +', ' ', text)
    # Remove lines starting with symbols
    lines = text.split('\n')
    clean_lines = [
        l.strip() for l in lines
        if l.strip() and len(l.strip()) > 5
    ]
    return ' '.join(clean_lines)


def score_sentence_with_model(question, sentence):
    """
    Use the QA model to score how well a sentence
    answers the question. Returns confidence score.
    """
    try:
        inputs = tokenizer(
            question,
            sentence,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )

        with torch.no_grad():
            outputs = model(**inputs)

        # Get the best answer span
        start = torch.argmax(outputs.start_logits)
        end = torch.argmax(outputs.end_logits) + 1

        if end <= start:
            end = start + 1

        # Decode answer
        tokens = inputs["input_ids"][0][start:end]
        answer = tokenizer.decode(tokens, skip_special_tokens=True).strip()

        # Calculate confidence
        start_prob = torch.softmax(
            outputs.start_logits, dim=1
        )[0][start].item()
        end_prob = torch.softmax(
            outputs.end_logits, dim=1
        )[0][end-1].item()
        confidence = (start_prob + end_prob) / 2

        return answer, confidence

    except Exception:
        return "", 0.0


def generate_answer_with_model(question, context):
    """
    Improved approach:
    1. Split context into clean sentences
    2. Score each sentence using the QA model
    3. Return the answer from the highest scoring sentence
    """
    try:
        if not context or not question:
            return None

        # Clean the context
        context = clean_for_model(context)

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', context)

        # Filter sentences
        good_sentences = []
        for s in sentences:
            s = s.strip()
            word_count = len(s.split())
            # Keep sentences with 8-100 words
            if 8 <= word_count <= 100:
                good_sentences.append(s)

        if not good_sentences:
            return None

        # Score each sentence with the model
        best_answer = None
        best_score = 0.0
        best_sentence = None

        for sentence in good_sentences[:10]:
            answer, score = score_sentence_with_model(
                question, sentence
            )

            # ✅ Fix 1: Remove question text from answer
            # Sometimes model includes the question in answer
            if answer.lower().startswith(question.lower()[:20].lower()):
                answer = answer[len(question):].strip()

            # ✅ Fix 2: Skip very short or ToC-like answers
            if re.match(r'^.*\bxi\b|\bxv\b|\bvii\b|\bviii\b', answer):
                continue

            if score > best_score and len(answer) > 3:
                best_score = score
                best_answer = answer
                best_sentence = sentence

        print(f"Best score: {best_score:.3f}")

        # If model found a good short answer return full sentence
        if best_answer and best_score > 0.1 and len(best_answer.split()) >= 3:
            if len(best_answer.split()) < 6 and best_sentence:
                # ✅ Fix 3: Clean the sentence before returning
                clean = best_sentence
                # Remove question prefix if present
                q_prefix = question.lower()[:15]
                if clean.lower().startswith(q_prefix):
                    clean = clean[len(question):].strip()
                return clean
            return best_answer

        if best_sentence and best_score > 0.05:
            clean = best_sentence
            q_prefix = question.lower()[:15]
            if clean.lower().startswith(q_prefix):
                clean = clean[len(question):].strip()
            return clean

        return None

    except Exception as e:
        print(f"QA model error: {e}")
        return None