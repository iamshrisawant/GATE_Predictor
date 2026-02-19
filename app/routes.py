from flask import Blueprint, request, jsonify, render_template, send_from_directory
import os
import shutil
import json
from .services import extraction, scoring, email_service

main_bp = Blueprint('main', __name__)

DATA_FOLDER = os.path.join(os.getcwd(), 'data')
LIVE_FOLDER = os.path.join(DATA_FOLDER, 'live')
STAGING_FOLDER = os.path.join(DATA_FOLDER, 'staging')
ADMIN_PIN = os.getenv("ADMIN_PIN")

# Ensure dirs exist
os.makedirs(LIVE_FOLDER, exist_ok=True)
os.makedirs(STAGING_FOLDER, exist_ok=True)

@main_bp.route('/')
def index():
    return render_template('index.html')



@main_bp.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@main_bp.route('/contribute')
def contribute():
    return render_template('contribute.html')

@main_bp.route('/api/detect_metadata', methods=['POST'])
def detect_meta():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    temp_path = os.path.join(DATA_FOLDER, "temp_" + file.filename)
    file.save(temp_path)
    
    try:
        meta = extraction.detect_metadata(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    return jsonify(meta)

@main_bp.route('/api/upload_paper', methods=['POST'])
def upload_paper():
    if 'answer_key' not in request.files:
        return jsonify({"error": "Answer Key file is required"}), 400
        
    key_file = request.files['answer_key']
    paper_file = request.files.get('question_paper')
    
    year = request.form.get('year', '2025')
    code = request.form.get('paper_code', '').upper()
    mode = request.form.get('mode', 'staging')
    admin_pin = request.headers.get('X-Admin-Pin', '')
    
    if not code:
        return jsonify({"error": "Paper Code is required"}), 400
        
    if mode == 'live':
        if admin_pin != ADMIN_PIN:
            return jsonify({"error": "Invalid Admin PIN for Live Upload"}), 403
        target_root = LIVE_FOLDER
    else:
        target_root = STAGING_FOLDER

    target_dir = os.path.join(target_root, year, code)
    os.makedirs(target_dir, exist_ok=True)
    
    key_path = os.path.join(target_dir, "answer_key.pdf")
    key_file.save(key_path)
    
    if paper_file:
        paper_path = os.path.join(target_dir, "question_paper.pdf")
        paper_file.save(paper_path)
        
    try:
        schema_path = os.path.join(target_dir, "schema.json")
        extraction.extract_answer_key(key_path, schema_path, paper_code=code)
        
        if mode == 'live':
             return jsonify({"message": f"Successfully published {code} ({year}) to LIVE!"})
        else:
            attachments = [key_path]
            if paper_file:
                attachments.append(paper_path)
            
            email_service.send_approval_email_async(year, code, attachments=attachments)
            return jsonify({"message": f"Submitted {code} ({year}) for review!"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/api/papers', methods=['GET'])
def list_papers():
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
            
            if os.path.exists(os.path.join(code_path, "schema.json")):
                tree[year].append(code)
    return jsonify(tree)

@main_bp.route('/api/calculate', methods=['POST'])
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
            
        report = scoring.calculate_score(url, schema)
        if "error" in report:
            return jsonify(report), 500
        return jsonify(report)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@main_bp.route('/api/check_paper_exists', methods=['GET'])
def check_paper_exists():
    year = request.args.get('year')
    code = request.args.get('code')
    if not year or not code:
        return jsonify({"exists": False})
    schema_path = os.path.join(LIVE_FOLDER, year, code.upper(), "schema.json")
    return jsonify({"exists": os.path.exists(schema_path)})

@main_bp.route('/api/staging_file')
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

@main_bp.route('/api/approve_token/<token>', methods=['GET'])
def approve_token(token):

    try:
        data = email_service.serializer.loads(token, salt="approve-paper", max_age=86400)
        year = data['year']
        code = data['code']
        
        src = os.path.join(STAGING_FOLDER, year, code)
        dst = os.path.join(LIVE_FOLDER, year, code)
        
        if not os.path.exists(src):
            return "Error: Paper not found in staging", 404
            
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        if os.path.exists(dst): shutil.rmtree(dst)
        shutil.move(src, dst)
        return f"<h1>Success!</h1><p>Paper {code} ({year}) has been approved and is now LIVE.</p><a href='/'>Go to App</a>"
    except Exception as e:
        return f"Invalid or Expired Token: {str(e)}", 400

@main_bp.route('/api/staging_queue', methods=['GET'])
def staging_queue():
    queue = []
    if not os.path.exists(STAGING_FOLDER):
        return jsonify(queue)
    for year in os.listdir(STAGING_FOLDER):
        year_path = os.path.join(STAGING_FOLDER, year)
        if not os.path.isdir(year_path): continue
        for code in os.listdir(year_path):
            queue.append({"year": year, "code": code})
    return jsonify(queue)

def verify_request_pin(req):
    pin = req.headers.get('X-Admin-Pin')
    if pin and pin == ADMIN_PIN: return True
    if req.is_json:
        data = req.json
        if data and data.get('pin') == ADMIN_PIN: return True
    return False

@main_bp.route('/api/verify_pin', methods=['POST'])
def verify_pin_route():
    data = request.json
    if data.get('pin') == ADMIN_PIN: return jsonify({"success": True})
    return jsonify({"success": False, "error": "Incorrect PIN"}), 401

@main_bp.route('/api/approve_paper', methods=['POST'])
def approve_paper():
    if not verify_request_pin(request): return jsonify({"error": "Unauthorized"}), 401
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

@main_bp.route('/api/reject_paper', methods=['POST'])
def reject_paper():
    if not verify_request_pin(request): return jsonify({"error": "Unauthorized"}), 401
    data = request.json
    year = data.get('year')
    code = data.get('code')
    src = os.path.join(STAGING_FOLDER, year, code)
    if os.path.exists(src):
        shutil.rmtree(src)
        return jsonify({"message": "Rejected"})
    return jsonify({"error": "Not found"}), 404

@main_bp.route('/api/live_papers', methods=['GET'])
def live_papers():
    papers = []
    if not os.path.exists(LIVE_FOLDER): return jsonify(papers)
    for year in os.listdir(LIVE_FOLDER):
        year_path = os.path.join(LIVE_FOLDER, year)
        if not os.path.isdir(year_path): continue
        for code in os.listdir(year_path):
            papers.append({"year": year, "code": code})
    papers.sort(key=lambda x: (x['year'], x['code']), reverse=True)
    return jsonify(papers)

@main_bp.route('/api/delete_live_paper', methods=['POST'])
def delete_live_paper():
    if not verify_request_pin(request): return jsonify({"error": "Unauthorized"}), 401
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
