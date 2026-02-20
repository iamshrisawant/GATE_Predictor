from bs4 import BeautifulSoup
import re

def inspect_q66():
    with open("test/GE.html", "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")
    
    # Q.66 is likely using image with 'q66' or it's the 66th question?
    # Schema says GE_66.
    # Regex searches for _ge...q66.
    # Let's search all tables for this pattern and print details.
    
    questions = soup.find_all("table", class_="questionPnlTbl")
    
    regex = re.compile(r"_ge[a-z0-9]*q66")
    
    for i, q_tbl in enumerate(questions):
        imgs = q_tbl.find_all("img")
        found = False
        for img in imgs:
            if regex.search(img.get("src", "") or img.get("name", "")):
                found = True
                break
        
        if found:
            print(f"Found Q.66 at Index {i}")
            
            # Print Options
            print("Options found in HTML:")
            for img in imgs:
                parent = img.find_parent("td")
                txt = parent.get_text(strip=True) if parent else "???"
                src = img.get("src", "")
                name = img.get("name", "")
                final = name if name else src.split("/")[-1]
                print(f"  Text: '{txt}', Image: '{final}'")
            
            # Print Menu table (User Answer)
            menu = q_tbl.find_next("table", class_="menu-tbl")
            if menu:
                print("Menu Table:")
                print(menu.get_text(strip=True, separator="|"))

if __name__ == "__main__":
    inspect_q66()
