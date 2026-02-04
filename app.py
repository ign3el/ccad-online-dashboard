
import os
import sqlite3
import json
# import pandas as pd # Disabled for local test
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.utils import secure_filename
from pypdf import PdfReader

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_me_in_prod'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'instance/rtls_kb.db'
app.config['PASSWORD'] = 'CCAD2026' # Simple password gate

# Ensure dirs exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs('instance', exist_ok=True)

def get_db_connection():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Users Table (RBAC)
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE,
                 password TEXT,
                 role TEXT -- 'admin' or 'client'
                 )''')
    
    # Knowledge Base Table
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_base (
                 id TEXT PRIMARY KEY,
                 type TEXT,
                 category TEXT,
                 question TEXT,
                 answer TEXT
                 )''')
    # Logs Table (Enhanced)
    c.execute('''CREATE TABLE IF NOT EXISTS support_logs (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 timestamp DATETIME,
                 resolved_at DATETIME,
                 operator TEXT,
                 asset_tag TEXT,
                 issue_category TEXT,
                 issue_description TEXT,
                 resolution_status TEXT,
                 root_cause TEXT
                 )''')
    c.execute('''CREATE TABLE IF NOT EXISTS equipment (
                 id TEXT PRIMARY KEY,
                 name TEXT,
                 type TEXT,
                 model TEXT,
                 manufacturer TEXT,
                 battery_life TEXT,
                 common_issues TEXT,
                 details TEXT
                 )''')
    
    # Default users
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'CCAD2026', 'admin')")
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('client', 'HONEYWELL', 'client')")
    
    conn.commit()
    return conn

# --- ROUTES ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        if user:
            session['logged_in'] = True
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Invalid Credentials')
    return render_template('login.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    try:
        data = request.json if request.is_json else request.form
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'error': 'Username and password required'}), 400
            
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        
        if user:
            session['logged_in'] = True
            session['username'] = user['username']
            session['role'] = user['role']
            return jsonify({'success': True, 'role': user['role']})
        else:
            return jsonify({'success': False, 'error': 'Invalid Credentials'}), 401
    except Exception as e:
        print(f"Login Error: {str(e)}")
        return jsonify({'success': False, 'error': 'Internal Server Error', 'details': str(e)}), 500

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html', user_role=session.get('role'))

# --- API: KNOWLEDGE BASE ---

@app.route('/api/kb', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_kb():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    
    if request.method == 'GET':
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 1000))
        sort_by = request.args.get('sort_by', 'id')
        order = request.args.get('order', 'asc')
        search = request.args.get('search', '')
        type_filter = request.args.get('type', '') # New Filter
        
        offset = (page - 1) * per_page
        
        allowed_sort = ['id', 'type', 'category', 'question']
        if sort_by not in allowed_sort: sort_by = 'id'
        if order not in ['asc', 'desc']: order = 'asc'

        # Dynamic Query Construction
        query = f"SELECT * FROM knowledge_base WHERE (question LIKE ? OR answer LIKE ? OR id LIKE ?)"
        params = [f"%{search}%", f"%{search}%", f"%{search}%"]
        
        if type_filter:
            query += " AND type = ?"
            params.append(type_filter)
            
        query += f" ORDER BY {sort_by} {order} LIMIT ? OFFSET ?"
        params.extend([per_page, offset])
        
        kb = conn.execute(query, params).fetchall()
        
        # Count Query
        count_query = "SELECT COUNT(*) FROM knowledge_base WHERE (question LIKE ? OR answer LIKE ? OR id LIKE ?)"
        count_params = [f"%{search}%", f"%{search}%", f"%{search}%"]
        if type_filter:
            count_query += " AND type = ?"
            count_params.append(type_filter)
            
        total = conn.execute(count_query, count_params).fetchone()[0]
        
        conn.close()
        return jsonify({
            'data': [dict(ix) for ix in kb],
            'total': total,
            'page': page,
            'per_page': per_page
        })
        
    if request.method == 'POST':
        data = request.json
        try:
            conn.execute('INSERT INTO knowledge_base (id, type, category, question, answer) VALUES (?, ?, ?, ?, ?)',
                         (data['id'], data['type'], data['category'], data['question'], data['answer']))
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    if request.method == 'PUT':
        data = request.json
        conn.execute('UPDATE knowledge_base SET type=?, category=?, question=?, answer=? WHERE id=?',
                     (data['type'], data['category'], data['question'], data['answer'], data['id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

    if request.method == 'DELETE':
        id = request.args.get('id')
        conn.execute('DELETE FROM knowledge_base WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

@app.route('/api/backup', methods=['GET', 'POST'])
def api_backup():
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'GET': # Export
        conn = get_db_connection()
        faq = conn.execute("SELECT * FROM knowledge_base WHERE type='faq'").fetchall()
        ts = conn.execute("SELECT * FROM knowledge_base WHERE type='troubleshooting'").fetchall()
        eq = conn.execute("SELECT * FROM equipment").fetchall()
        conn.close()
        return jsonify({
            'faq': [dict(ix) for ix in faq],
            'troubleshooting': [dict(ix) for ix in ts],
            'equipment': [dict(ix) for ix in eq]
        })
        
    if request.method == 'POST': # Import
        file = request.files.get('file')
        if not file: return jsonify({'error': 'No file'}), 400
        
        try:
            data = json.load(file)
            conn = get_db_connection()
            # Batch import for FAQ, TS, Equipment
            for faq in data.get('faq', []):
                conn.execute('INSERT OR REPLACE INTO knowledge_base (id, type, category, question, answer) VALUES (?, ?, ?, ?, ?)',
                             (faq['id'], 'faq', faq['category'], faq['question'], faq['answer']))
            
            for ts in data.get('troubleshooting', []):
                conn.execute('INSERT OR REPLACE INTO knowledge_base (id, type, category, question, answer) VALUES (?, ?, ?, ?, ?)',
                             (ts['id'], 'troubleshooting', ts['category'], ts['title'], json.dumps(ts)))
            
            for eq in data.get('equipment', []):
                conn.execute('INSERT OR REPLACE INTO equipment (id, name, type, model, manufacturer, battery_life, common_issues, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                             (eq['id'], eq['name'], eq['type'], eq['model'], eq['manufacturer'], eq.get('battery_life'), json.dumps(eq.get('common_issues', [])), json.dumps(eq)))
            
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

# --- API: LOGS ---
@app.route('/api/logs', methods=['GET', 'POST'])
def api_logs():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    if request.method == 'GET':
        logs = conn.execute('SELECT * FROM support_logs ORDER BY timestamp DESC').fetchall()
        conn.close()
        return jsonify([dict(ix) for ix in logs])

    data = request.json
    conn.execute('INSERT INTO support_logs (timestamp, operator, asset_tag, issue_category, issue_description, resolution_status, root_cause) VALUES (?, ?, ?, ?, ?, ?, ?)',
                 (datetime.now(), data.get('operator', session.get('username')), data['asset_tag'], data['category'], data['description'], data['status'], data.get('root_cause', 'Unknown')))

    conn.commit()
    conn.close()
    return jsonify({'success': True})

# --- API: ANALYTICS ---
@app.route('/api/analytics', methods=['GET'])
def api_analytics():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    
    # 1. Total Calls
    total = conn.execute('SELECT COUNT(*) FROM support_logs').fetchone()[0]
    
    # 2. Top Categories
    cats = conn.execute('SELECT issue_category, COUNT(*) as count FROM support_logs GROUP BY issue_category ORDER BY count DESC').fetchall()
    categories = [{'issue_category': r[0], 'count': r[1]} for r in cats]
    
    # 3. Asset Issues
    assets = conn.execute("SELECT asset_tag, COUNT(*) as count FROM support_logs WHERE asset_tag IS NOT NULL AND asset_tag != '' GROUP BY asset_tag ORDER BY count DESC LIMIT 5").fetchall()
    top_assets = [{'asset_tag': r[0], 'count': r[1]} for r in assets]

    # 4. Operator Performance
    operators = conn.execute('SELECT operator, COUNT(*) as count FROM support_logs GROUP BY operator ORDER BY count DESC').fetchall()
    top_operators = [{'operator': r[0], 'count': r[1]} for r in operators]

    conn.close()
    return jsonify({
        'total_calls': total,
        'categories': categories,
        'top_assets': top_assets,
        'top_operators': top_operators
    })

# --- API: EQUIPMENT ---
@app.route('/api/equipment', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_equipment():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    
    if request.method == 'GET':
        items = conn.execute('SELECT * FROM equipment').fetchall()
        result = []
        for row in items:
            r = dict(row)
            result.append(r)
        conn.close()
        return jsonify({'data': result})

    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    if request.method == 'POST':
        data = request.json
        conn.execute('INSERT INTO equipment (id, name, type, model, manufacturer, battery_life, common_issues, details) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                     (data['id'], data['name'], data['type'], data['model'], data['manufacturer'], data.get('battery_life'), json.dumps(data.get('common_issues', [])), json.dumps(data)))
        conn.commit()
    
    if request.method == 'PUT':
        data = request.json
        conn.execute('UPDATE equipment SET name=?, type=?, model=?, manufacturer=?, battery_life=?, common_issues=?, details=? WHERE id=?',
                     (data['name'], data['type'], data['model'], data['manufacturer'], data.get('battery_life'), json.dumps(data.get('common_issues', [])), json.dumps(data), data['id']))
        conn.commit()

    if request.method == 'DELETE':
        id = request.args.get('id')
        conn.execute('DELETE FROM equipment WHERE id = ?', (id,))
        conn.commit()

    conn.close()
    return jsonify({'success': True})

# --- API: USERS (Admin Only) ---
@app.route('/api/users', methods=['GET', 'POST', 'DELETE'])
def api_users():
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_connection()
    if request.method == 'GET':
        users = conn.execute('SELECT id, username, role FROM users').fetchall()
        conn.close()
        return jsonify([dict(ix) for ix in users])
    # ... POST/DELETE for user management ...
    conn.close()
    return jsonify({'success': True})

# --- API: AUTO-KB (UPLOAD) ---
@app.route('/api/upload', methods=['POST'])
def api_upload():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    if 'file' not in request.files: return jsonify({'error': 'No file'}), 400
    
    file = request.files['file']
    if file.filename == '': return jsonify({'error': 'No file selected'}), 400
    
    filename = secure_filename(file.filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(path)
    
    # Simple Extraction Logic
    try:
        reader = PdfReader(path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        # Heuristic Parsing (Placeholder logic for demo)
        # We assume paragraphs starting with "Problem:" are questions
        new_entries = []
        lines = text.split('\n')
        current_q = None
        current_a = ""
        
        for line in lines:
            if "Problem:" in line or "Issue:" in line:
                if current_q:
                   new_entries.append({"question": current_q, "answer": current_a, "type": "Troubleshooting"})
                current_q = line.strip()
                current_a = ""
            elif current_q:
                current_a += line + "\n"
                
        # Commit to DB as "Drafts" (tagged with [DRAFT])
        conn = get_db_connection()
        count = 0
        for entry in new_entries:
            draft_id = f"DRAFT-{int(datetime.now().timestamp())}-{count}"
            conn.execute('INSERT INTO knowledge_base (id, type, category, question, answer) VALUES (?, ?, ?, ?, ?)',
                         (draft_id, entry['type'], 'Pending Review', entry['question'], entry['answer']))
            count += 1
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'count': count})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5101, debug=True)
