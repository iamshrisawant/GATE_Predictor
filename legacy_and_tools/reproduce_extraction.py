import re

def test_extraction(text, filename):
    meta = {"paper_code": ""}
    
    print(f"--- Testing: {filename} ---")
    print(f"Text Snippet: {text[:100]}...")

    # CURRENT LOGIC FROM extract_answer_key.py (Simplified for testing)
    
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
            # Limit to standard codes to avoid capturing (Q.1) etc.
            codes = "AE|AG|AR|BM|BT|CE|CH|CS|CY|DA|EC|EE|ES|EY|GE|GG|IN|MA|ME|MN|MT|NM|PE|PH|PI|ST|TF|XE|XH|XL"
            code_match = re.search(rf"\((({codes})\d?)\)", text[:500])

    if code_match:
        meta["paper_code"] = code_match.group(1).upper()
        print(f"MATCH: {meta['paper_code']}")
    else:
        print("NO MATCH via Text")
        
        # Filename Fallback
        codes = "AE|AG|AR|BM|BT|CE|CH|CS|CY|DA|EC|EE|ES|EY|GE|GG|IN|MA|ME|MN|MT|NM|PE|PH|PI|ST|TF|XE|XH|XL"
        # Match matches code + optional digit (e.g. CS1, ME2)
        # Removed trailing \b because CS1Key.pdf has no boundary between 1 and K
        c_match = re.search(rf"({codes})(\d?)", filename, re.IGNORECASE)
        if c_match:
            suffix = c_match.group(2) if c_match.group(2) else ""
            meta["paper_code"] = c_match.group(1).upper() + suffix
            print(f"MATCH via Filename: {meta['paper_code']}")
        else:
             print("NO MATCH via Filename either")
    print("-" * 20)

def test_filename_extraction(filename):
    print(f"--- Testing Filename: {filename} ---")
    
    codes = "AE|AG|AR|BM|BT|CE|CH|CS|CY|DA|EC|EE|ES|EY|GE|GG|IN|MA|ME|MN|MT|NM|PE|PH|PI|ST|TF|XE|XH|XL"
    
    # Priority 1: Code + Digit (Single digit, not part of a larger number like 25)
    c_match = re.search(rf"({codes})([1-9])(?!\d)", filename, re.IGNORECASE)
    
    if c_match:
        code = c_match.group(1).upper() + c_match.group(2)
        print(f"MATCH (Priority 1): {code}")
    else:
        # Priority 2: Just Code
        c_match = re.search(rf"({codes})", filename, re.IGNORECASE)
        if c_match:
            print(f"MATCH (Priority 2): {c_match.group(1).upper()}")
        else:
            print("NO MATCH")

# Test Cases provided by User (latest)
samples = [
    (
        "Answer Key for Data Science and Artificial Intelligence (DA)", 
        "R505D99-DA25S52051073-answerKey.pdf"
    ),
    (
        "Computer Science & Information Technology (CS1)", 
        "CS1Key.pdf"
    ),
    (
        "Answer Key for Computer Science and Information Technology 1 (CS1)", 
        "CS1_Keys.pdf"
    ),
    (
        "Answer Key for Computer Science and Information Technology 2 (CS2)", 
        "CS2_Keys.pdf"
    )
]

# Run text extraction test
for text, fname in samples:
    test_extraction(text, fname)

print("\n=== FILENAME ONLY TEST ===")
filenames = [s[1] for s in samples]
for fname in filenames:
    test_filename_extraction(fname)
