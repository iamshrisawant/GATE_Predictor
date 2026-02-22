import sys
import os
import json

sys.path.append(os.getcwd())
import app.services.extraction as extraction

pairs = [
    {
        "code": "EC",
        "key": "test/G412P96-EC26S72105100-answerKey.pdf",
        "paper": "test/G412P96-EC26S72105100-questionPaper.pdf"
    },
    {
        "code": "CS",
        "key": "test/G368E21-CS26S42101001-answerKey.pdf",
        "paper": "test/G412P96-EC26S72105100-questionPaper.pdf" # note user provided EC paper for CS in prompt
    },
    {
        "code": "DA",
        "key": "test/G368E21-DA26S82101040-answerKey.pdf",
        "paper": "test/G368E21-DA26S82101040-questionPaper.pdf"
    }
]

def run_tests():
    for p in pairs:
        print(f"\n--- Testing {p['code']} ---")
        try:
            with open(p['key'], 'rb') as kf, open(p['paper'], 'rb') as pf:
                schema = extraction.extract_answer_key(kf, paper_code=p['code'], paper_source=pf)
                print(f"Extracted {len(schema)} keys for {p['code']}.")
                
                # Check sample values
                if len(schema) > 0:
                    first_key = list(schema.keys())[0]
                    last_key = list(schema.keys())[-1]
                    print(f"Sample First: {schema[first_key]}")
                    print(f"Sample Last:  {schema[last_key]}")
        except Exception as e:
            print(f"Failed {p['code']}: {e}")

if __name__ == '__main__':
    run_tests()
