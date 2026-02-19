import re

def test_filename_extraction(filename):
    print(f"--- Testing Filename: {filename} ---")
    
    codes = "AE|AG|AR|BM|BT|CE|CH|CS|CY|DA|EC|EE|ES|EY|GE|GG|IN|MA|ME|MN|MT|NM|PE|PH|PI|ST|TF|XE|XH|XL"
    # UPDATED LOGIC (No boundaries)
    c_match = re.search(rf"({codes})(\d?)", filename, re.IGNORECASE)
    
    if c_match:
        suffix = c_match.group(2) if c_match.group(2) else ""
        code = c_match.group(1).upper() + suffix
        print(f"MATCH: {code}")
    else:
        print("NO MATCH")

# Test Cases provided by User
filenames = [
    "R505D99-DA25S52051073-answerKey.pdf",
    "CS1Key.pdf",
    "CS1_Keys.pdf",
    "CS2_Keys.pdf"
]

for fname in filenames:
    test_filename_extraction(fname)
