import json
import re
from bs4 import BeautifulSoup

def compare_keys():
    html_path = "test/GE.html"
    schema_path = "test/schema (1).json"
    
    # Load Schema Keys
    with open(schema_path, "r") as f:
        schema = json.load(f)
    schema_keys = set(schema.keys())
    print(f"Schema Keys: {len(schema_keys)}")
    
    # Extract HTML Keys using the FIXED regex
    # Regex from scoring.py: rf"_{re.escape(subj.lower())}[a-z0-9]*q(\d+)"
    # We need to extract subjects from schema first
    active_subjects = set()
    for k in schema_keys:
        if "_" in k: active_subjects.add(k.split("_")[0])
    
    subject_regexes = {}
    for subj in active_subjects:
        pattern = rf"_{re.escape(subj.lower())}[a-z0-9]*q(\d+)"
        subject_regexes[subj] = re.compile(pattern)
        
    extracted_keys = set()
    
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            
        questions = soup.find_all("table", class_="questionPnlTbl")
        print(f"HTML Question Tables: {len(questions)}")
        
        for i, q_tbl in enumerate(questions):
            imgs = q_tbl.find_all("img")
            found_ref = None
            for img in imgs:
                src = img.get("src", "")
                name = img.get("name", "")
                final_name = name if name else src.split("/")[-1]
                check_str = final_name.lower()
                
                for subj, regex in subject_regexes.items():
                    match = regex.search(check_str)
                    if match:
                        q_num = int(match.group(1))
                        found_ref = f"{subj}_{q_num}"
                        break
                if found_ref: break
            
            if found_ref:
                extracted_keys.add(found_ref)
            else:
                print(f"WARNING: No key extracted for Q Table index {i}")
                
        print(f"Extracted HTML Keys: {len(extracted_keys)}")
        
        # Compare
        missing_in_schema = extracted_keys - schema_keys
        missing_in_html = schema_keys - extracted_keys
        
        if missing_in_schema:
            print(f"HTML keys NOT in Schema: {missing_in_schema}")
        else:
            print("All HTML keys are present in Schema.")
            
        if missing_in_html:
            print(f"Schema keys NOT in HTML: {missing_in_html}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    compare_keys()
