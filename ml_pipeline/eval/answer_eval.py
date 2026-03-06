"""
LLM-as-judge evaluation of answer quality.
"""

import json
import re

from groq import Groq
from ml_pipeline.monitoring.logger import JSONLogger

logger = JSONLogger()


def evaluate_answer(question: str, answer: str) -> dict:
    """Score the generated answer on relevance, clarity, and insight."""
    from app.config import settings

    prompt = (
        "Given the following question and the answer provided, score the answer.\n\n"
        f"Question: {question}\n\nAnswer:\n{answer}\n\n"
        "Return a JSON object with these keys:\n"
        "- relevance (0-10): Does the answer address the question?\n"
        "- clarity (0-10): Is it clear and readable?\n"
        "- insight (0-10): Does it offer a useful observation beyond the literal answer?\n"
        "- reasoning: One sentence explanation.\n\n"
        "Return only valid JSON. Example: "
        "{\"relevance\": 9, \"clarity\": 8, \"insight\": 6, \"reasoning\": \"...\"}"
    )

    messages = [{"role": "user", "content": prompt}]

    try:
        client = Groq(api_key=settings.groq_api_key)
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=messages,
            temperature=0,
            max_tokens=256,
        )
        text = response.choices[0].message.content.strip()
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            scores = json.loads(match.group())
            return {
                "relevance": float(scores.get("relevance", 5)) / 10,
                "clarity": float(scores.get("clarity", 5)) / 10,
                "insight": float(scores.get("insight", 5)) / 10,
                "reasoning": scores.get("reasoning", ""),
            }
    except Exception as exc:
        logger.log("answer_eval_error", {"error": str(exc)})

    return {
        "relevance": 0.5,
        "clarity": 0.5,
        "insight": 0.5,
        "reasoning": "Eval unavailable.",
    }
