import sys
import os
import json

# Correct sys.path to include the root directory
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
# We also need to add the parent of 'backend' if we are in backend/
# The project structure is:
# PharmaIQ1.0/
#   backend/
#   chat_pipeline/
#   eval_and_metrics/

sys.path.insert(0, os.getcwd())

from eval_and_metrics.eval.answer_eval import evaluate_answer

question = "What is the total NRx count across all HCPs?"
answer = "The total NRx count across all HCPs is 8,322."
sql_result = '[{"total_nrx": 8322.0}]'

print("Running evaluate_answer...")
result = evaluate_answer(question, answer, sql_result)
print("Result:", json.dumps(result, indent=2))
