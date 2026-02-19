import pdfplumber
import json
import re
import os

def extract_answer_key(pdf_path, output_path, paper_code=None):
    schema = {}
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                # Skip header row if it contains "Q.No." or "Question No"
                start_idx = 0
                if table[0][0] and ("No" in table[0][0] or "Session" in table[0][0]):
                    start_idx = 1
                
                for row in table[start_idx:]:
                    if not row or len(row) < 6:
                        continue
                    
                    # Row format: [Q.No, Session, Que.Type, Sec. Name, Key, Marks]
                    q_no = row[0]
                    session = row[1]
                    q_type = row[2]
                    section = row[3]
                    key = row[4]
                    marks = row[5]

                    # Standardize Section Name for Regex Matching (GA, CS, DA, etc.)
                    raw_section = section.strip()
                    clean_section = raw_section
                    
                    # 1. General Aptitude -> GA
                    if "general aptitude" in raw_section.lower():
                        clean_section = "GA"
                    # 2. If we have a paper_code (e.g. CS) and section is NOT GA, assume it's the subject
                    # This handles "Computer Science..." -> "CS"
                    elif paper_code and raw_section.lower() != "ga":
                        # If the raw section is the full name or matches code
                        clean_section = paper_code

                    schema_key = f"{clean_section}_{q_no}"
                    
                    schema[schema_key] = {
                        "question_no": int(q_no),
                        "section": clean_section,
                        "original_section": raw_section,
                        "question_type": q_type,
                        "key": key,
                        "marks": float(marks)
                    }

    print(f"Extracted {len(schema)} keys.")
    if output_path:
        with open(output_path, "w") as f:
            json.dump(schema, f, indent=4)
        print(f"Saved schema to {output_path}")
    
    return schema

    return schema

def detect_metadata(pdf_path):
    """
    Attempts to extract Year, Paper Code, and Set from PDF filename or content.
    Returns dict: {'year': str, 'paper_code': str, 'set_no': str}
    """
    filename = os.path.basename(pdf_path)
    meta = {
        "year": "", 
        "paper_code": ""
    }
    
    
    # 1. Try Content First (Most Reliable)
    try:
        with pdfplumber.open(pdf_path) as pdf:
            # Check first page text
            # Check first page text
            text = pdf.pages[0].extract_text()
            if text:
                # Year: "GATE 2025" or just "2024" if GATE missing
                y_match = re.search(r"GATE\s?(\d{4})", text, re.IGNORECASE)
                if y_match:
                    meta["year"] = y_match.group(1)
                else:
                    # Fallback: look for 202x in first page
                    y_weak = re.search(r"\b(202\d)\b", text)
                    if y_weak:
                        meta["year"] = y_weak.group(1)

                # Paper Code: "Answer Key for ... (DA)" or "(CS1)"
                # User Request: Extract DA, CS1, CS2 directly.
                # Regex matches (Letters + Optional Digit) inside parens
                # Regex matches (Letters + Optional Digit) inside parens
                # Pattern 1: Answer Key for ... (CS1)
                code_match = re.search(r"Answer Key for .* \(([A-Z]{2}\d?)\)", text)
                
                # Pattern 2: Paper Code : CS1 (or just Code : CS1)
                if not code_match:
                     code_match = re.search(r"(?:Paper )?Code\s?:\s?([A-Z]{2}\d?)", text, re.IGNORECASE)

                # Pattern 3: Subject : ... (DA)
                if not code_match:
                     code_match = re.search(r"Subject\s?:\s?.* \(([A-Z]{2}\d?)\)", text, re.IGNORECASE)

                # Pattern 4: Generic Parens (Use with caution -> Now Standard)
                if not code_match:
                     # Look for (CS1) or (DA) explicitly.
                     # Removed 500 char limit to ensure we catch it even if header is long.
                     codes = "AE|AG|AR|BM|BT|CE|CH|CS|CY|DA|EC|EE|ES|EY|GE|GG|IN|MA|ME|MN|MT|NM|PE|PH|PI|ST|TF|XE|XH|XL"
                     code_match = re.search(rf"\((({codes})\d?)\)", text)

                if code_match:
                    meta["paper_code"] = code_match.group(1).upper()
                    
                # Special Handling for Multi-Session Papers (CS, ME, CE, etc.)
                # If code is like "CS" but text says "Session 1" or "Shift 1", make it "CS1"
                if meta["paper_code"] and not meta["paper_code"][-1].isdigit():
                    session_match = re.search(r"(?:Session|Shift)\s?(\d)", text, re.IGNORECASE)
                    if session_match:
                        meta["paper_code"] += session_match.group(1)
            
    except Exception as e:
        print(f"Error reading PDF content: {e}")

    # 2. Fallback to Filename if missing
    if meta["year"] == "2025": # If still default (or we want to confirm)
        # Check for DA25, CS25 etc.
        y_short = re.search(r"([A-Z]{2})(\d{2})", filename) 
        if y_short:
             # If we see DA25, it's 2025. 
             meta["year"] = "20" + y_short.group(2)
        else:
             # Check for GATE2025 or similar specific pattern
             y_full = re.search(r"GATE[-_]?\s?(20\d{2})", filename, re.IGNORECASE)
             if y_full:
                 meta["year"] = y_full.group(1)

    if not meta["paper_code"]:
        codes = "AE|AG|AR|BM|BT|CE|CH|CS|CY|DA|EC|EE|ES|EY|GE|GG|IN|MA|ME|MN|MT|NM|PE|PH|PI|ST|TF|XE|XH|XL"
        
        # Priority 1: Code + Digit (Single digit, not part of a larger number like 25)
        # Matches CS1, CS2 but avoids DA2 in DA25
        c_match = re.search(rf"({codes})([1-9])(?!\d)", filename, re.IGNORECASE)
        
        if c_match:
             meta["paper_code"] = c_match.group(1).upper() + c_match.group(2)
        else:
            # Priority 2: Just Code
            c_match = re.search(rf"({codes})", filename, re.IGNORECASE)
            if c_match:
                meta["paper_code"] = c_match.group(1).upper()
            
    # Filename Set match fallback - REMOVED as per user request to simplify
    # if meta["set_no"] == "1":
    #    s_match = re.search(r"[A-Z]{2}\d{2}S(\d)", filename)
    #    if s_match:
    #        meta["set_no"] = s_match.group(1)
            
    return meta

if __name__ == "__main__":
    # Test
    # extract_answer_key("R505D99-DA25S52051073-answerKey.pdf", "answer_key_schema.json")
    pass
