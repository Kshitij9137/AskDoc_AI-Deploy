import re
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# ── Load Flan-T5 Large ─────────────────────────
# First run downloads ~3GB — be patient!
MODEL_NAME = "google/flan-t5-large"

print("Loading Flan-T5 generative model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
model.eval()
print("Flan-T5 loaded! ✅")


def clean_context(text):
    """
    Clean context before sending to generative model.
    Remove bullet symbols, API paths, and short noise lines.
    """
    text = re.sub(r'[◦▪•●▸▹►◆▷]', ' ', text)
    text = re.sub(r'(POST|GET|PUT|DELETE)\s+/api/\S+', '', text)
    text = re.sub(r'Page No\.\s*\S+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'CCET\s+IPS', '', text, flags=re.IGNORECASE)

    lines = text.split('\n')
    clean = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if len(line.split()) < 4:
            continue
        if re.match(r'^[\d\s\.\-]+$', line):
            continue
        clean.append(line)

    text = ' '.join(clean)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def generate_answer_with_model(question, context):
    """
    Flan-T5 with corrected prompt format.
    Flan-T5 works best with simple direct instructions,
    not complex multi-line prompts.
    """
    try:
        context = clean_context(context)

        if not context or not question:
            return None

        # Trim context
        words = context.split()
        if len(words) > 400:
            context = ' '.join(words[:400])

        # ✅ Flan-T5 works best with this simple format
        prompt = f"answer the question from the context. context: {context} question: {question}"

        inputs = tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=512
        )

        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=150,
                num_beams=4,
                early_stopping=True,
                no_repeat_ngram_size=2,
            )

        answer = tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

        print(f"Flan-T5 raw answer: {answer[:120]}")

        # Reject bad answers
        bad_responses = [
            'document does not contain',
            'document does not provide',
            'not mentioned',
            'not provided',
            'no information',
            'cannot answer',
            'i don\'t know',
            'not found',
        ]

        answer_lower = answer.lower()
        if any(bad in answer_lower for bad in bad_responses):
            print("Flan-T5 said not found — trying shorter context...")

            # Try again with first 200 words only
            short_context = ' '.join(words[:200])
            short_prompt = f"answer the question from the context. context: {short_context} question: {question}"

            short_inputs = tokenizer(
                short_prompt,
                return_tensors="pt",
                truncation=True,
                max_length=512
            )

            with torch.no_grad():
                short_outputs = model.generate(
                    **short_inputs,
                    max_new_tokens=150,
                    num_beams=4,
                    early_stopping=True,
                )

            answer = tokenizer.decode(
                short_outputs[0], skip_special_tokens=True
            ).strip()

            print(f"Flan-T5 retry answer: {answer[:120]}")

            # If still bad, give up
            if any(bad in answer.lower() for bad in bad_responses):
                return None

        # Validate final answer
        if answer and len(answer.split()) >= 3:
            return answer

        return None

    except Exception as e:
        print(f"Flan-T5 error: {e}")
        return None