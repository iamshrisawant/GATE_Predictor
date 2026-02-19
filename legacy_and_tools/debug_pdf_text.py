import pdfplumber
import re

pdf_path = r"data/2025/DA/answer_key.pdf"

print(f"--- EXTRACTING TEXT FROM {pdf_path} ---")
try:
    with pdfplumber.open(pdf_path) as pdf:
        text = pdf.pages[0].extract_text()
        print(text[:1000])
        
        print("\n--- REGEX TESTS ---")
        patterns = [
            r"Answer Key for .* \(([A-Z]{2}\d?)\)",
            r"(?:Paper )?Code\s?:\s?([A-Z]{2}\d?)",
            r"Subject\s?:\s?.* \(([A-Z]{2}\d?)\)",
            r"\(([A-Z]{2}\d?)\)"
        ]
        
        for p in patterns:
            match = re.search(p, text, re.IGNORECASE)
            print(f"Pattern '{p}': {match.group(1) if match else 'NO MATCH'}")

except Exception as e:
    print(f"Error: {e}")
