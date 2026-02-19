from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import os
import json
import extract_answer_key
import calculate_score
import shutil

from dotenv import load_dotenv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
import threading

# Load Env
load_dotenv()

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)


DATA_FOLDER = os.path.join(os.getcwd(), 'data') # Use CWD for safety
LIVE_FOLDER = os.path.join(DATA_FOLDER, 'live')
STAGING_FOLDER = os.path.join(DATA_FOLDER, 'staging')

os.makedirs(LIVE_FOLDER, exist_ok=True)
os.makedirs(STAGING_FOLDER, exist_ok=True)

# Configuration
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
ADMIN_PIN = os.getenv("ADMIN_PIN", "GATE2025") # Default fallback
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5000")

# Secret Key
app.secret_key = os.getenv("SECRET_KEY", "dev-secret-key")

from itsdangerous import URLSafeTimedSerializer
serializer = URLSafeTimedSerializer(app.secret_key)

def send_approval_email(year, code, attachments=None):
    token = serializer.dumps({"year": year, "code": code, "action": "approve"}, salt="approve-paper")
    approve_link = f"{BASE_URL}/api/approve_token/{token}"
    
    subject = f"GATE Predictor: New Submission {code} ({year})"
    body = f"""
    <h2>New Submission for Review</h2>
    <p>A new paper has been uploaded to the staging area.</p>
    <ul>
        <li><strong>Paper Code:</strong> {code}</li>
        <li><strong>Year:</strong> {year}</li>
    </ul>
    <p>
        <a href="{approve_link}" style="background:#10b981; color:white; padding:10px 20px; text-decoration:none; border-radius:5px;">
            Approve & Publish Live
        </a>
    </p>
    <p>Or visit the <a href="{BASE_URL}/dashboard">Admin Dashboard</a> to review.</p>
    """
    
    print(f"\n[EMAIL DEBUG] To Admin ({SMTP_EMAIL}):\nSubject: {subject}\nLink: {approve_link}\n")
    
    if SMTP_EMAIL and SMTP_PASSWORD:
        try:
            msg = MIMEMultipart()
            msg['From'] = f"GATE Predictor <{SMTP_EMAIL}>"
            msg['To'] = SMTP_EMAIL
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            
            # Attach files if provided
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                            part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                            msg.attach(part)
            
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_EMAIL, SMTP_PASSWORD)
                server.send_message(msg)
            print("[EMAIL] Sent successfully.")
        except Exception as e:
            print(f"[EMAIL ERROR] Failed to send: {e}")
    else:
        print("[EMAIL WARNING] SMTP credentials not set. Email skipped.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/api/detect_metadata', methods=['POST'])
def detect_meta():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    # Save temp to read
    temp_path = os.path.join(DATA_FOLDER, "temp_" + file.filename)
    file.save(temp_path)
    
    try:
        meta = extract_answer_key.detect_metadata(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
            
    return jsonify(meta)

@app.route('/api/upload_paper', methods=['POST'])
def upload_paper():
    # Expects: answer_key, question_paper (optional), year, paper_code
    if 'answer_key' not in request.files:
        return jsonify({"error": "Answer Key file is required"}), 400
        
    key_file = request.files['answer_key']
    paper_file = request.files.get('question_paper')
    
    year = request.form.get('year', '2025')
    code = request.form.get('paper_code', '').upper()
    mode = request.form.get('mode', 'staging') # staging or live
    admin_pin = request.headers.get('X-Admin-Pin', '')
    
    if not code:
        return jsonify({"error": "Paper Code is required"}), 400
        
    # Determine Target Folder
    if mode == 'live':
        if admin_pin != ADMIN_PIN: # Environment variable check
            return jsonify({"error": "Invalid Admin PIN for Live Upload"}), 403
        target_root = LIVE_FOLDER
    else:
        target_root = STAGING_FOLDER

    # Create Directory
    target_dir = os.path.join(target_root, year, code)
    os.makedirs(target_dir, exist_ok=True)
    
    # Save Key
    key_path = os.path.join(target_dir, "answer_key.pdf")
    key_file.save(key_path)
    
    # Save Paper (if provided)
    if paper_file:
        paper_path = os.path.join(target_dir, "question_paper.pdf")
        paper_file.save(paper_path)
        
    try:
        # Generate Schema
        schema_path = os.path.join(target_dir, "schema.json")
        extract_answer_key.extract_answer_key(key_path, schema_path, paper_code=code)
        
        if mode == 'live':
             return jsonify({"message": f"Successfully published {code} ({year}) to LIVE!"})
        else:
            # SEND EMAIL NOTIFICATION with Attachments (ASYNC)
            attachments = [key_path]
            if paper_file:
                attachments.append(paper_path)
            
            # Run email in background thread to prevent blocking
            email_thread = threading.Thread(target=send_approval_email, args=(year, code, attachments))
            email_thread.start()
            
            return jsonify({"message": f"Submitted {code} ({year}) for review!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/papers', methods=['GET'])
def list_papers():
    # Return hierarchy: { "2025": ["CS", "DA", "CS1", "CS2"], ... }
    tree = {}
    # Return hierarchy: { "2025": ["CS", "DA", "CS1", "CS2"], ... }
    tree = {}
    if not os.path.exists(LIVE_FOLDER):
        return jsonify(tree)
        
    for year in os.listdir(LIVE_FOLDER):
        year_path = os.path.join(LIVE_FOLDER, year)
        if not os.path.isdir(year_path): continue
        
        tree[year] = []
        for code in os.listdir(year_path):
            code_path = os.path.join(year_path, code)
            if not os.path.isdir(code_path): continue
            
            # Check if valid schema exists
            if os.path.exists(os.path.join(code_path, "schema.json")):
                tree[year].append(code)
                    
    return jsonify(tree)

@app.route('/api/calculate', methods=['POST'])
def calculate():
    data = request.json
    url = data.get('url')
    year = data.get('year')
    code = data.get('paper_code')
    
    if not all([url, year, code]):
        return jsonify({"error": "Missing required fields (url, year, code)"}), 400
    
    schema_path = os.path.join(LIVE_FOLDER, year, code, "schema.json")
    
    if not os.path.exists(schema_path):
        return jsonify({"error": "Paper not found on server."}), 404
        
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)
            
        report = calculate_score.calculate_score(url, schema)
        if "error" in report:
            return jsonify(report), 500
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/check_paper_exists', methods=['GET'])
def check_paper_exists():
    year = request.args.get('year')
    code = request.args.get('code')
    
    if not year or not code:
        return jsonify({"exists": False})
        
    # Check if schema exists in LIVE
    schema_path = os.path.join(LIVE_FOLDER, year, code.upper(), "schema.json")
    exists = os.path.exists(schema_path)
    
    # Also check STAGING? For now, let's just warn if it's already in LIVE.
    # If in staging, maybe let them re-upload (overwrite staging).
    
    return jsonify({"exists": exists})

@app.route('/api/staging_file')
def staging_file():
    year = request.args.get('year')
    code = request.args.get('code')
    filename = request.args.get('file')
    
    if not (year and code and filename):
        return "Missing parameters", 400
        
    directory = os.path.join(STAGING_FOLDER, year, code)
    if not os.path.exists(directory):
        return "Paper not found", 404
        
    return send_from_directory(directory, filename)

@app.route('/api/approve_token/<token>', methods=['GET'])
def approve_token(token):
    try:
        data = serializer.loads(token, salt="approve-paper", max_age=86400) # 24h expiry
        year = data['year']
        code = data['code']
        
        src = os.path.join(STAGING_FOLDER, year, code)
        dst = os.path.join(LIVE_FOLDER, year, code)
        
        if not os.path.exists(src):
            return "Error: Paper not found in staging (already approved or rejected?)", 404
            
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst):
            shutil.rmtree(dst) # Overwrite existing
        
        shutil.move(src, dst)
        return f"<h1>Success!</h1><p>Paper {code} ({year}) has been approved and is now LIVE.</p><a href='/'>Go to App</a>"
        
    except Exception as e:
        return f"Invalid or Expired Token: {str(e)}", 400

@app.route('/api/staging_queue', methods=['GET'])
def staging_queue():
    queue = []
    if not os.path.exists(STAGING_FOLDER):
        return jsonify(queue)
        
    for year in os.listdir(STAGING_FOLDER):
        year_path = os.path.join(STAGING_FOLDER, year)
        if not os.path.isdir(year_path): continue
        
        for code in os.listdir(year_path):
            # In a real app, we'd store timestamp. For now, just list them.
            queue.append({"year": year, "code": code})
    return jsonify(queue)


def verify_request_pin(req):
    """Helper to verify PIN from headers or request body"""
    # Check Header
    pin = req.headers.get('X-Admin-Pin')
    if pin and pin == ADMIN_PIN:
        return True
        
    # Check JSON body (fallback)
    if req.is_json:
        data = req.json
        if data and data.get('pin') == ADMIN_PIN:
            return True
            
    return False

@app.route('/api/verify_pin', methods=['POST'])
def verify_pin_route():
    data = request.json
    pin = data.get('pin')
    if pin == ADMIN_PIN:
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Incorrect PIN"}), 401

@app.route('/api/approve_paper', methods=['POST'])
def approve_paper():
    if not verify_request_pin(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    year = data.get('year')
    code = data.get('code')
    
    src = os.path.join(STAGING_FOLDER, year, code)
    dst = os.path.join(LIVE_FOLDER, year, code)
    
    if not os.path.exists(src): return jsonify({"error": "Not found"}), 404
    
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if os.path.exists(dst): shutil.rmtree(dst)
    shutil.move(src, dst)
    
    return jsonify({"message": "Approved"})

@app.route('/api/reject_paper', methods=['POST'])
def reject_paper():
    if not verify_request_pin(request):
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    year = data.get('year')
    code = data.get('code')
    
    src = os.path.join(STAGING_FOLDER, year, code)
    if os.path.exists(src):
        shutil.rmtree(src)
        return jsonify({"message": "Rejected"})
    return jsonify({"error": "Not found"}), 404

@app.route('/api/live_papers', methods=['GET'])
def live_papers():
    # List all papers in LIVE_FOLDER
    papers = []
    if not os.path.exists(LIVE_FOLDER):
        return jsonify(papers)
        
    for year in os.listdir(LIVE_FOLDER):
        year_path = os.path.join(LIVE_FOLDER, year)
        if not os.path.isdir(year_path): continue
        
        for code in os.listdir(year_path):
            # Check if valid paper dir (contains schema/keys)
            # Not strictly checking content, just directory existence
            papers.append({"year": year, "code": code})
            
    # Sort by Year desc, then Code asc
    papers.sort(key=lambda x: (x['year'], x['code']), reverse=True)
    return jsonify(papers)

@app.route('/api/delete_live_paper', methods=['POST'])
def delete_live_paper():
    if not verify_request_pin(request):
        return jsonify({"error": "Unauthorized"}), 401
    
    data = request.json
    year = data.get('year')
    code = data.get('code')
    
    target = os.path.join(LIVE_FOLDER, year, code)
    
    if os.path.exists(target):
        try:
            shutil.rmtree(target)
            return jsonify({"message": f"Deleted {code} ({year}) from Live."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
            
    return jsonify({"error": "Paper not found"}), 404
    
@app.route('/contribute')
def contribute():
    return render_template('contribute.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, port=5000)
