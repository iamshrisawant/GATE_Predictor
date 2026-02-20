from bs4 import BeautifulSoup
import re

def find_q8_images():
    html_path = "test/GE.html"
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")
            
        imgs = soup.find_all("img")
        print(f"Found {len(imgs)} images.")
        
        q8_regex = re.compile(r"q8(?=\.jpg)", re.IGNORECASE)
        
        found = False
        for img in imgs:
            name = img.get("name", "")
            src = img.get("src", "")
            
            # Check name first
            if q8_regex.search(name):
                print(f"MATCH (name): {name}")
                found = True
            elif q8_regex.search(src):
                 print(f"MATCH (src): {src}")
                 found = True

        if not found:
            print("No images matching 'q8' found.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    find_q8_images()
