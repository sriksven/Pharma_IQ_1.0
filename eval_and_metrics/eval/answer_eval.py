"""
LLM-as-judge evaluation of answer quality.
"""

import json
import re

from groq import Groq
from eval_and_metrics.monitoring.logger import JSONLogger

logger = JSONLogger()

GROQ_JUDGE_MODEL = "openai/gpt-oss-120b"
GROQ_FALLBACK_MODEL = "openai/gpt-oss-20b"

def _truncate_reasoning(text: str) -> str:
    if not text:
        return ""
    return text[:1000]

def evaluate_answer(question: str, answer: str, sql_result: str | None = None) -> dict:
    """Score the generated answer on relevance, clarity, insight, and faithfulness to the data payload."""
    from app.config import settings

    prompt = (
        "You are an evaluator for a pharmaceutical data assistant.\n\n"
        "Given the following question, the data payload returned from the database, and the AI's final answer, score the answer's quality.\n\n"
        f"Question: {question}\n\n"
        f"SQL Data Payload:\n{sql_result}\n\n"
        f"Assistant Answer:\n{answer}\n\n"
        "Score the answer on these dimensions (0-10):\n"
        "- relevance: Does the answer directly address the question?\n"
        "- clarity: Is the answer easy to read and understand?\n"
        "- insight: Does it provide useful context or highlight meaningful data?\n"
        "- faithfulness: DEDUCT points if the answer claims something NOT in the Data Payload or hallucinates numbers.\n"
        "- reasoning: One sentence explanation.\n\n"
        "Return ONLY a clean JSON object. Example:\n"
        "{\"relevance\": 9, \"clarity\": 10, \"insight\": 7, \"faithfulness\": 10, \"reasoning\": \"...\"}"
    )

    messages = [{"role": "user", "content": prompt}]
    client = Groq(api_key=settings.groq_api_key)

    try:
        response = client.chat.completions.create(
            model=GROQ_JUDGE_MODEL,
            messages=messages,
            temperature=0,
            max_tokens=512,
        )
        text = response.choices[0].message.content.strip()
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            scores = json.loads(match.group())
            return {
                "relevance": float(scores.get("relevance", 5)) / 10,
                "clarity": float(scores.get("clarity", 5)) / 10,
                "insight": float(scores.get("insight", 5)) / 10,
                "faithfulness": float(scores.get("faithfulness", 5)) / 10,
                "reasoning": _truncate_reasoning(scores.get("reasoning", "")),
            }
    except Exception as exc:
        logger.log("answer_eval_error", {"step": "primary", "error": str(exc)})
        
        try:
            response = client.chat.completions.create(
                model=GROQ_FALLBACK_MODEL,
                messages=messages,
                temperature=0,
                max_tokens=256,
            )
            text = response.choices[0].message.content.strip()
            text = re.sub(r'```json\s*', '', text)
            text = re.sub(r'```\s*', '', text)
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                scores = json.loads(match.group())
                return {
                    "relevance": float(scores.get("relevance", 5)) / 10,
                    "clarity": float(scores.get("clarity", 5)) / 10,
                    "insight": float(scores.get("insight", 5)) / 10,
                    "faithfulness": float(scores.get("faithfulness", 5)) / 10,
                    "reasoning": scores.get("reasoning", ""),
                }
        except Exception as fallback_exc:
            logger.log("answer_eval_error", {"step": "fallback", "error": str(fallback_exc)})

    return {
        "relevance": None,
        "clarity": None,
        "insight": None,
        "faithfulness": None,
        "reasoning": "Eval unavailable.",
    }
