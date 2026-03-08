import os
import sys
import re
import csv


# Adjust Python path so we can import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app.config import settings, _PROJECT_ROOT
from chat_pipeline.retry import run_with_retry
from data_pipeline.ingest import load_all_tables
from data_pipeline.registry import build_registry
from chat_pipeline.db import init_db
import asyncio

def parse_sample_questions(filepath):
    """Parses sample_questions.md and extracts the question/expected answer pairs."""
    questions = []
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Match lines like: **1. What is the total NRx count across all HCPs?**
    # Followed immediately by: > ~8,322 new prescriptions...
    pattern = re.compile(r'\*\*\d+\.\s+(.*?)\*\*\n>\s+(.*?)(?=\n\n|\Z)', re.DOTALL)
    
    matches = pattern.findall(content)
    for index, (q, a) in enumerate(matches):
        questions.append({
            "id": index + 1,
            "question": q.strip().replace("\n", " "),
            "expected_logic": a.strip().replace("\n", " ")
        })
        
    return questions


def run_gold_eval(questions):
    """
    Runs the deterministic Gold Standard evaluation.
    For each question, pushes it through the SQL generator and measures Execution Success Rate.
    """
    results = []
    total_latency = 0
    successful = 0

    print(f"Starting Gold Eval on {len(questions)} questions...\n")

    for idx, item in enumerate(questions):
        q = item["question"]
        print(f"[{idx+1}/{len(questions)}] Q: {q}")
        
        try:
            import time
            
            # We don't cache locally here to get raw performance
            start_t = time.time()
            result_df, sql, llm_used, retry_count, sql_error, sql_system_prompt = run_with_retry(
                q, conversation_history=None
            )
            latency_ms = int((time.time() - start_t) * 1000)
            
            # Deterministic Metric: Execution Success
            valid_execution = result_df is not None and sql_error is None
            
            results.append({
                "id": item["id"],
                "question": q,
                "expected_logic": item["expected_logic"],
                "generated_sql": sql if sql else "None",
                "execution_success": valid_execution,
                "latency_ms": latency_ms,
                "retry_count": retry_count,
                "error": sql_error if sql_error else "None"
            })
            
            total_latency += latency_ms
            if valid_execution:
                successful += 1
                print(f"  ✓ Success ({latency_ms}ms)")
            else:
                print(f"  ✗ Failed: {sql_error}")
                
        except Exception as e:
            print(f"  ✗ Critical Exception: {e}")
            results.append({
                "id": item["id"],
                "question": q,
                "expected_logic": item["expected_logic"],
                "generated_sql": "Exception",
                "execution_success": False,
                "latency_ms": 0,
                "retry_count": 0,
                "error": str(e)
            })

    # Save to CSV
    output_file = os.path.join(_PROJECT_ROOT, "backend", "gold_eval_results.csv")
    with open(output_file, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "question", "expected_logic", "generated_sql", 
            "execution_success", "latency_ms", "retry_count", "error"
        ])
        writer.writeheader()
        writer.writerows(results)

    # Print summary
    success_rate = (successful / len(questions)) * 100
    avg_latency = total_latency / len(questions)
    
    print("\n" + "="*40)
    print("🥇 GOLD EVALUATION COMPLETE")
    print("="*40)
    print(f"Total Questions: {len(questions)}")
    print(f"Execution Success Rate: {success_rate:.1f}%")
    print(f"Average Latency: {avg_latency:.1f} ms")
    print(f"Full report saved to: {output_file}")


async def main():
    md_path = os.path.join(_PROJECT_ROOT, "docs", "sample_questions.md")
    if not os.path.exists(md_path):
        print(f"Error: Could not find sample questions at {md_path}")
        sys.exit(1)
        
    print("Initialize DB and loading data...")
    await init_db()
    tables = load_all_tables(settings.data_dir)
    build_registry(tables, settings.data_dir)
    print("Data loaded successfully. Starting evaluations...")

    questions = parse_sample_questions(md_path)
    # We only run the first 10 for speed in generic tests, change this to run all 50 if desired.
    run_gold_eval(questions[:10])

if __name__ == "__main__":
    asyncio.run(main())
