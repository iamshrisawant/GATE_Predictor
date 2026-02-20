import sys
import os
import json

sys.path.append(os.getcwd())
from app.services import extraction

def extract_and_check():
    pdf_path = "test/GE_Keys.pdf"
    if not os.path.exists(pdf_path):
        print(f"Error: {pdf_path} not found.")
        return

    print(f"Extracting keys from {pdf_path}...")
    try:
        with open(pdf_path, "rb") as f:
            # extract_answer_key expects a stream
            schema = extraction.extract_answer_key(f, paper_code="GE")
        
        print(f"Extraction complete. Found {len(schema)} keys.")
        
        # Check for GE_8
        if "GE_8" in schema:
            print(f"SUCCESS: GE_8 found in new schema! Key: {schema['GE_8']}")
        else:
            print("FAILURE: GE_8 NOT found in new schema.")
            
        # Check GA_8
        if "GA_8" in schema:
             print(f"GA_8 found: {schema['GA_8']}")
             
        # Save new schema
        with open("test/schema_fixed.json", "w") as f:
            json.dump(schema, f, indent=4)
        print("Saved extracted schema to test/schema_fixed.json")
        
    except Exception as e:
        print(f"Extraction failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    extract_and_check()
