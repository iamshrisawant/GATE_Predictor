import json
import os
import sys

# Add the current directory to sys.path to make imports work
sys.path.append(os.getcwd())

from app.services import scoring

def debug_scoring():
    html_path = r"test/GE.html"
    schema_path = r"test/schema (1).json"

    # Load schema
    with open(schema_path, "r") as f:
        schema = json.load(f)

    # Calculate score
    report = scoring.calculate_score(html_path, schema)

    if "error" in report:
        print(f"Error: {report['error']}")
        return

    print(f"{'Q':<10} | {'Type':<5} | {'Key':<15} | {'User':<15} | {'Result':<10} | {'Marks':<6}")
    print("-" * 75)

    for d in report['details']:
        print(f"{d['Q']:<10} | {d['Type']:<5} | {str(d['Key']):<15} | {str(d['User']):<15} | {d['Result']:<10} | {d['Marks']:<6}")

    s = report['summary']
    print("-" * 75)
    print(f"Total Score: {s['total_score']}")
    print(f"Attempted: {s['attempted']}")
    print(f"Correct: {s['correct']}")
    print(f"Wrong: {s['wrong']}")
    print(f"Total Questions: {s['total_questions']}")

if __name__ == "__main__":
    debug_scoring()
