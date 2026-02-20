import pdfplumber
import sys

def debug_pdf():
    pdf_path = "test/GE_Keys.pdf"
    print(f"Inspecting {pdf_path}...")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                print(f"--- Page {i+1} ---")
                tables = page.extract_tables()
                print(f"Found {len(tables)} tables.")
                
                for t_idx, table in enumerate(tables):
                    print(f"Table {t_idx+1}:")
                    for r_idx, row in enumerate(table):
                        # print raw row to see what's happening
                        print(f"  Row {r_idx}: {row}")
                        
                        # Check strictly for Question 8
                        if row and len(row) > 0 and str(row[0]).strip() == "8":
                            print(f"  >>> FOUND POTENTIAL Q.8: {row}")
                            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_pdf()
