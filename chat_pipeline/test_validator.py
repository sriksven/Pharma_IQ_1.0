import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from chat_pipeline.sql_validator import validate_sql

def run_tests():
    print("Running sql validator tests...")
    
    # Valid query
    valid_query = "SELECT territory_id, SUM(total_trx) as sales FROM fact_ln_metrics GROUP BY territory_id"
    errs = validate_sql(valid_query)
    print(f"Valid query errs (expect empty): {errs}")
    
    # Hallucinated column
    bad_col = "SELECT est_market_share FROM territory_dim LIMIT 5"
    errs = validate_sql(bad_col)
    print(f"Bad column errs: {errs}")
    
    # Hallucinated table
    bad_table = "SELECT * FROM imaginary_table"
    errs = validate_sql(bad_table)
    print(f"Bad table errs: {errs}")

if __name__ == "__main__":
    run_tests()
