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

def evaluate_answer(question: str, answer: str, sql_result: str | None = None) -> dict:
    """Score the generated answer on relevance, clarity, insight, and faithfulness to the data payload."""
    from app.config import settings

    prompt = (
        "Given the following question, the data returned from the database, and the AI's final answer, score the answer.\n\n"
        f"Question: {question}\n\nSQL Result Data:\n{sql_result}\n\nAnswer:\n{answer}\n\n"
        "Return a JSON object with these keys:\n"
        "- relevance (0-10): Does the answer specifically address the question?\n"
        "- clarity (0-10): Is it clear and readable?\n"
        "- insight (0-10): Does it offer a useful, logically sound observation?\n"
        "- faithfulness (0-10): DEDUCT points severely if the answer hallucinates numbers, facts, or claims that are NOT present in the SQL Result Data. Does it strictly adhere to the data payload provided without making things up?\n"
        "- reasoning: One sentence explanation.\n\n"
        "Return only valid JSON. Example: "
        "{\"relevance\": 9, \"clarity\": 8, \"insight\": 6, \"faithfulness\": 10, \"reasoning\": \"...\"}"
    )

    messages = [{"role": "user", "content": prompt}]
    client = Groq(api_key=settings.groq_api_key)

    try:
        response = client.chat.completions.create(
            model=GROQ_JUDGE_MODEL,
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
