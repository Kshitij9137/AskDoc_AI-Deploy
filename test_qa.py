import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'askdocs_backend.settings')
django.setup()

from qa_engine.pipeline import answer_question

questions = [
    "What is AskDocs AI?",
    "What is the problem definition?",
    "What is the objective of this project?",
    "What technologies are used?",
    "What is semantic search?",
    "What is FAISS used for?",
    "What are the functional requirements?",
    "What is JWT authentication?",
    "What is sentence transformer?",
    "What is the system workflow?",
]

noise_words = ['page no', 'ccet ips', 'submitted by', 'batch year', 'enrolment']

passed = 0
failed = 0

for i, q in enumerate(questions, 1):
    result = answer_question(q)
    answer = result['answer']

    has_noise = any(n in answer.lower() for n in noise_words)
    is_short = len(answer.split()) < 10
    is_fallback = 'could not find' in answer.lower()

    if has_noise or is_fallback:
        status = '❌'
        failed += 1
    elif is_short:
        status = '⚠️'
        failed += 1
    else:
        status = '✅'
        passed += 1

    print(f"\n{status} Q{i}: {q}")
    print(f"   A: {answer[:200]}")

print(f"\n{'='*50}")
print(f"Results: {passed}/10 passed | {failed}/10 failed")