import json
import re
from bs4 import BeautifulSoup
import sys
import requests

def parse_range(key_range):
    """Parses NAT range string like '24 to 24' or '0.25 to 0.28'."""
    try:
        parts = key_range.split(" to ")
        if len(parts) == 2:
            return float(parts[0]), float(parts[1])
        return float(key_range), float(key_range)
    except ValueError:
        return None, None

def calculate_score(html_path, schema_data_or_path):
    if isinstance(schema_data_or_path, str):
        with open(schema_data_or_path, "r") as f:
            schema = json.load(f)
    else:
        schema = schema_data_or_path

    # Extract active subjects from schema keys (e.g., "GA_1" -> "GA")
    active_subjects = set()
    for k in schema.keys():
        if "_" in k:
            active_subjects.add(k.split("_")[0])
    
    # Pre-compile regexes for efficiency
    # Pattern: _{subject_lower}\d*q(\d+)
    # e.g., GA -> _ga\d*q(\d+)
    subject_regexes = {}
    for subj in active_subjects:
        pattern = rf"_{subj.lower()}\d*q(\d+)"
        subject_regexes[subj] = re.compile(pattern)

    if html_path.startswith("http"):
         # Already handled in main, but good for library usage
         pass
    
    # Read HTML content
    if html_path.startswith("http"):
        try:
             r = requests.get(html_path)
             r.raise_for_status()
             soup = BeautifulSoup(r.text, "html.parser")
        except Exception as e:
             return {"error": str(e)}
    else:
        with open(html_path, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f, "html.parser")

    questions = soup.find_all("table", class_="questionPnlTbl")
    
    # 2. Map User Responses to Master Questions via Image Name
    # This is the most reliable method as image names like "..._ga5q2.jpg" directly match the Master Key.
    
    total_score = 0
    attempted = 0
    correct = 0
    wrong = 0
    details = []

    # Main Processing Loop
    questions = soup.find_all("table", class_="questionPnlTbl")
    # print(f"Processing {len(questions)} questions from HTML...")

    for i, q_tbl in enumerate(questions):
        # 1. Extract Question ID and Status
        q_id = None
        status = "Not Attempted"
        user_ans = None
        
        menu_tbl = q_tbl.find_next("table", class_="menu-tbl")
        if menu_tbl:
            cols = menu_tbl.find_all("td")
            for k in range(0, len(cols), 2):
                if k+1 >= len(cols): break
                label = cols[k].text.strip()
                val = cols[k+1].text.strip()
                
                if "Question ID" in label:
                    q_id = val
                elif "Status" in label:
                    status = val
                elif "Chosen Option" in label:
                    user_ans = val
                elif "Given Answer" in label:
                    user_ans = val

        # Fallback for NAT Answer (hidden in questionRowTbl)
        if user_ans is None:
            q_row_tbl = q_tbl.find("table", class_="questionRowTbl")
            if q_row_tbl:
                tds = q_row_tbl.find_all("td")
                for k in range(len(tds)-1):
                    txt = tds[k].text.strip()
                    if "Given Answer" in txt and ":" in txt:
                        user_ans = tds[k+1].text.strip()
                        break
        
        # Normalize Answer
        if user_ans == "--" or not user_ans:
            user_ans = None

        # 2. Extract Master Question Number AND Option Mapping
        # Look for pattern based on dynamic subjects
        master_q_ref = None # e.g. "GA_1"
        option_map = {} # {'A': 'a', 'B': 'd', ...}
        
        imgs = q_tbl.find_all("img")
        for img in imgs:
            src = img.get("src", "")
            name = img.get("name", "")
            final_name = name if name else src.split("/")[-1]
            check_str = final_name.lower()
            
            # Check for Option Images first
            parent_td = img.find_parent("td")
            if parent_td:
                txt = parent_td.get_text(strip=True)
                opt_label = None
                if txt.startswith("A.") or txt.startswith("(A)"): opt_label = "A"
                elif txt.startswith("B.") or txt.startswith("(B)"): opt_label = "B"
                elif txt.startswith("C.") or txt.startswith("(C)"): opt_label = "C"
                elif txt.startswith("D.") or txt.startswith("(D)"): opt_label = "D"
                
                if opt_label:
                    base = final_name.rsplit('.', 1)[0]
                    suffix = base[-1].lower()
                    if suffix in ['a','b','c','d']:
                        option_map[opt_label] = suffix
                    continue

            # If not an option, check for Question ID Pattern using dynamic regexes
            # Only check if we haven't found the master ref yet (or maybe we should check all? 
            # No, usually one Q ref per question. But we must NOT break the outer loop so we find options)
            if not master_q_ref:
                for subj, regex in subject_regexes.items():
                    match = regex.search(check_str)
                    if match:
                        q_num = int(match.group(1))
                        master_q_ref = f"{subj}_{q_num}"
                        break
        
        if not master_q_ref:
            continue

        # 3. Retrieve Key and Score
        if master_q_ref not in schema:
            print(f"Error: mapped key {master_q_ref} not in schema!")
            continue
            
        q_data = schema[master_q_ref]
        
        # --- KEY MAPPING LOGIC START ---
        # Determine the "User-Facing Key" (Display Key) based on Shuffle Mapping
        official_key = q_data["key"]
        q_type = q_data["question_type"]
        max_marks = q_data["marks"]

        display_key = official_key # Default to master key (e.g. for NAT)

        if q_type == "MCQ":
            # Map Master Key (e.g. 'B') to User Option (e.g. 'C')
            target_suffix = official_key.lower().strip()
            # Find which User Option has this suffix
            mapped_label = None
            if option_map:
                for u_opt, suffix in option_map.items():
                    if suffix == target_suffix:
                         mapped_label = u_opt
                         break
            if mapped_label:
                display_key = mapped_label

        elif q_type == "MSQ":
            # Map Master Key (e.g. 'A;C') to User Options (e.g. 'B;D')
            off_suffixes = [x.strip().lower() for x in official_key.replace(";", ",").split(",") if x.strip()]
            mapped_labels = []
            
            if option_map:
                for suff in off_suffixes:
                    # Find user option for this suffix
                    for u_opt, map_suff in option_map.items():
                        if map_suff == suff:
                            mapped_labels.append(u_opt)
            
            # If we found mappings, sort and use them
            if mapped_labels:
                display_key = ";".join(sorted(mapped_labels))
            else:
                # Fallback: maybe options exist but mapping failed? Or generic MSQ?
                # Sort official key just in case
                display_key = ";".join(sorted([x.strip() for x in official_key.replace(";", ",").split(",") if x.strip()]))

        # --- SCORING LOGIC ---
        if user_ans:
            attempted += 1
            is_correct = False
            marks_gained = 0.0

            if q_type == "MCQ":
                # Compare User Ans directly to Display Key (since display_key IS the mapped correct option)
                if user_ans == display_key:
                    is_correct = True
                    marks_gained = max_marks
                else:
                    is_correct = False
                    # Negative marking
                    if max_marks == 1:
                        marks_gained = -1/3
                    elif max_marks == 2:
                        marks_gained = -2/3
            
            elif q_type == "MSQ":
                # Compare Sets of Options
                # Normalize user answer
                u_opts = sorted([x.strip() for x in user_ans.replace(";", ",").split(",") if x.strip()])
                target_opts = sorted([x.strip() for x in display_key.replace(";", ",").split(",") if x.strip()])
                
                if u_opts == target_opts:
                    is_correct = True
                    marks_gained = max_marks
                else:
                    is_correct = False
                    marks_gained = 0
            
            elif q_type == "NAT":
                # NAT logic unchanged (Range Parsing)
                try:
                    u_val = float(user_ans)
                    low, high = parse_range(official_key)
                    if low is not None and low <= u_val <= high + 1e-9:
                        is_correct = True
                        marks_gained = max_marks
                    else:
                        is_correct = False
                        marks_gained = 0
                except:
                    is_correct = False
                    marks_gained = 0
            
            if is_correct:
                correct += 1
            else:
                wrong += 1
            
            total_score += marks_gained
            
            details.append({
                "Q": master_q_ref,
                "Type": q_type,
                "Status": status,
                "User": user_ans,
                "Key": display_key, # Correct Mapped Key!
                "MasterKey": official_key, # Debugging Info
                "Result": "Correct" if is_correct else "Wrong",
                "Marks": marks_gained
            })
        else:
            # Unattempted
            marks_gained = 0.0
            
            details.append({
                "Q": master_q_ref,
                "Type": q_type,
                "Status": status,
                "User": "Not Attempted",
                "Key": display_key, # Show what they SHOULD have picked
                "MasterKey": official_key,
                "Result": "Unattempted",
                "Marks": marks_gained
            })

    # Create a summary dict
    report = {
        "summary": {
            "total_questions": len(details),
            "attempted": attempted,
            "correct": correct,
            "wrong": wrong,
            "total_score": total_score
        },
        "details": details
    }
    
    print(f"Total Score: {total_score:.2f}")
    
    with open("score_report.json", "w") as f:
        json.dump(report, f, indent=4)
        
    return report

if __name__ == "__main__":
    inp = "DA25S52051073_GATE2454S5D1979E1.html"
    if len(sys.argv) > 1:
        inp = sys.argv[1]
    
    if inp.startswith("http"):
        print(f"Fetching from URL: {inp}")
        try:
            r = requests.get(inp)
            r.raise_for_status()
            with open("temp_response.html", "w", encoding="utf-8") as f:
                f.write(r.text)
            inp = "temp_response.html"
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
            
    calculate_score(inp, "answer_key_schema.json")
