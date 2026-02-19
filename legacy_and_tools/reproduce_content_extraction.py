import re

def test_content_extraction(text, case_name):
    print(f"--- Testing Case: {case_name} ---")
    print(f"Text: '{text}'")
    
    meta = {"paper_code": ""}
    
    # LOGIC FROM extract_answer_key.py
    
    # Pattern 1: Answer Key for ... (CS1)
    code_match = re.search(r"Answer Key for .* \(([A-Z]{2}\d?)\)", text)
    
    # Pattern 2: Paper Code : CS1 (or just Code : CS1)
    if not code_match:
            code_match = re.search(r"(?:Paper )?Code\s?:\s?([A-Z]{2}\d?)", text, re.IGNORECASE)

    # Pattern 3: Subject : ... (DA)
    if not code_match:
            code_match = re.search(r"Subject\s?:\s?.* \(([A-Z]{2}\d?)\)", text, re.IGNORECASE)

    # Pattern 4: Generic Parens (Use with caution)
    if not code_match:
            # Look for (CS1) or (DA) explicitly in first 500 chars
            codes = "AE|AG|AR|BM|BT|CE|CH|CS|CY|DA|EC|EE|ES|EY|GE|GG|IN|MA|ME|MN|MT|NM|PE|PH|PI|ST|TF|XE|XH|XL"
            code_match = re.search(rf"\((({codes})\d?)\)", text[:500])

    if code_match:
        meta["paper_code"] = code_match.group(1).upper()
        # Special Handling for Multi-Session Papers (CS, ME, CE, etc.)
        if meta["paper_code"] and not meta["paper_code"][-1].isdigit():
            session_match = re.search(r"(?:Session|Shift)\s?(\d)", text, re.IGNORECASE)
            if session_match:
                meta["paper_code"] += session_match.group(1)
        
        print(f"MATCH: {meta['paper_code']}")
    else:
        print("NO MATCH")
    print("-" * 20)

# User Provided Examples
samples = [
    (
        "Answer Key for Data Science and Artificial Intelligence (DA)", 
        "GATE DA (Standard)"
    ),
    (
        "Computer Science & Information Technology (CS1)", 
        "CS1Key.pdf Content (No 'Answer Key for')"
    ),
    (
        "Answer Key for Computer Science and Information Technology 1 (CS1)", 
        "CS1_Keys.pdf Content"
    ),
    (
        "Answer Key for Computer Science and Information Technology 2 (CS2)", 
        "CS2_Keys.pdf Content"
    )
]

for text, name in samples:
    test_content_extraction(text, name)
