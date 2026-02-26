
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
                 details TEXT
                 )''')

    # FTS5 Virtual Table for Search
    try:
        c.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS wiki_fts USING fts5(
                        kb_id UNINDEXED, 
                        content, 
                        category, 
                        source, 
                        title,
                        tokenize = 'porter unicode61'
                    )''')
    except Exception: pass
    
    # Default users
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('admin', 'CCAD2026', 'admin')")
    c.execute("INSERT OR IGNORE INTO users (username, password, role) VALUES ('client', 'HONEYWELL', 'client')")
    
    conn.commit()
    return conn

# --- HELPERS ---

def update_wiki_index(kb_id, content, category, source, title):
    conn = get_db_connection()
    try:
        conn.execute('DELETE FROM wiki_fts WHERE kb_id = ?', (kb_id,))
        conn.execute('INSERT INTO wiki_fts (kb_id, content, category, source, title) VALUES (?, ?, ?, ?, ?)',
                     (kb_id, content, category, source, title))
        conn.commit()
    except Exception as e:
        print(f"Bsearch Error Syncing: {e}")
    finally:
        conn.close()

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
            update_wiki_index(data['id'], data['answer'], data['category'], data['type'], data['question'])
            conn.close()
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 400

    if request.method == 'PUT':
        data = request.json
        conn.execute('UPDATE knowledge_base SET type=?, category=?, question=?, answer=? WHERE id=?',
                     (data['type'], data['category'], data['question'], data['answer'], data['id']))
        conn.commit()
        update_wiki_index(data['id'], data['answer'], data['category'], data['type'], data['question'])
        conn.close()
        return jsonify({'success': True})

    if request.method == 'DELETE':
        id = request.args.get('id')
        conn.execute('DELETE FROM knowledge_base WHERE id = ?', (id,))
        conn.execute('DELETE FROM wiki_fts WHERE kb_id = ?', (id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

def preprocess_query(query):
    # Remove special FTS5 characters and split into keywords
    keywords = [k for k in query.replace('"', ' ').replace('*', ' ').replace('(', ' ').replace(')', ' ').split() if len(k) > 1]
    # Filter stopwords (basic set)
    stopwords = {'how', 'to', 'create', 'a', 'with', 'all', 'the', 'is', 'of', 'and', 'for', 'in'}
    filtered = [k for k in keywords if k.lower() not in stopwords]
    if not filtered: return query
    # Join with OR for maximum coverage
    return " OR ".join(filtered)

# --- API: WIKI SEARCH (FTS5) ---
@app.route('/api/wiki/search', methods=['GET'])
def api_wiki_search():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    query = request.args.get('q', '')
    if not query: return jsonify({'data': [], 'total': 0})
    
    conn = get_db_connection()
    
    # Pre-process for better matching
    smart_query = preprocess_query(query)
    
    # FTS5 search
    try:
        results = conn.execute('''
            SELECT kb_id, content, category, source, title, bm25(wiki_fts) as rank
            FROM wiki_fts 
            WHERE wiki_fts MATCH ? 
            ORDER BY rank 
            LIMIT 20''', (smart_query,)).fetchall()
    except Exception as e:
        # Fallback if FTS5 syntax fails
        results = conn.execute('''
            SELECT kb_id, content, category, source, title, -1.0 as rank
            FROM wiki_fts 
            WHERE content LIKE ? 
            LIMIT 20''', (f'%{query}%',)).fetchall()
    
    conn.close()
    
    return jsonify({
        'data': [dict(ix) for ix in results],
        'total': len(results)
    })

import requests

def call_groq_ai(prompt, system_prompt="You are a CCAD RTLS Tier 1 Support Assistant."):
    api_key = os.getenv('GROQ_API_KEY', '').strip()
    if not api_key:
        return {"error": "GROQ_API_KEY not set in environment."}
    
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": 1024
    }
    
    try:
        # Hardened timeout for stability
        res = requests.post(url, json=payload, headers=headers, timeout=20)
        if res.status_code != 200:
            print(f"Groq API Error ({res.status_code}): {res.text}")
        res.raise_for_status()
        return res.json()['choices'][0]['message']['content']
    except Exception as e:
        print(f"API Exception: {str(e)}")
        return f"AI Error: {str(e)}"

@app.route('/api/wiki/analyze', methods=['POST'])
def api_wiki_analyze():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    log_id = data.get('id')
    desc = data.get('description', '')
    
    # RAG: 1. Search Knowledge Base for context
    conn = get_db_connection()
    # Use smart pre-processing for better matches
    smart_q = preprocess_query(desc)
    
    results = conn.execute('''
        SELECT title, content, source 
        FROM wiki_fts 
        WHERE wiki_fts MATCH ? 
        LIMIT 5''', (smart_q,)).fetchall()
    conn.close()
    
    context = "\n".join([f"Source: {r['source']} | Title: {r['title']}\nContent: {r['content']}" for r in results])
    
    prompt = f"""
USER ISSUE LOG:
{desc}

RELEVANT KNOWLEDGE BASE CONTEXT:
{context if context else 'No direct matching guides found in the library.'}

TASK:
Analyze the issue using the provided context. 
If a solution is found in the context, describe it clearly for a Tier 1 engineer.
If no context matches, provide a best-effort diagnostic starting with hardware checks (power/attachment).

RESPONSE FORMAT (JSON-like):
Provide your answer in two sections:
1. VERIFIED_FIX: The technical solution.
2. MENTOR_TIP: A short, practical tip for the field engineer.
"""
    
    try:
        ai_response = call_groq_ai(prompt)
        
        # Parse AI response (basic extraction if LLM doesn't return strict JSON)
        fix = "Consult documentation."
        tip = "Escalate to T2 if unsure."
        
        if isinstance(ai_response, str) and "VERIFIED_FIX:" in ai_response:
            parts = ai_response.split("MENTOR_TIP:")
            fix = parts[0].replace("VERIFIED_FIX:", "").strip()
            if len(parts) > 1:
                tip = parts[1].strip()
        else:
            fix = str(ai_response) # Fallback to raw response or error dict
        
        return jsonify({
            'verified_fix': fix,
            'mentor_tip': tip,
            'source': "Groq Llama-3 (Sovereign AI)"
        })
    except Exception as e:
        print(f"CRITICAL ANALYZE ERROR: {str(e)}")
        return jsonify({'error': str(e)}), 500






@app.route('/api/wiki/summarize', methods=['POST'])
def api_wiki_summarize():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    data = request.json
    query = data.get('query', '').strip()
    results = data.get('results', [])
    
    # 1. Fetch Bible Context first to see if we have specific data
    conn = get_db_connection()
    bible_context = ""
    if not results and query:
        smart_q = preprocess_query(query)
        try:
            db_results = conn.execute('''
                SELECT title, content, source 
                FROM wiki_fts 
                WHERE wiki_fts MATCH ? 
                LIMIT 5''', (smart_q,)).fetchall()
            results = [dict(ix) for ix in db_results]
        except Exception:
            db_results = conn.execute('''
                SELECT title, content, source 
                FROM wiki_fts 
                WHERE content LIKE ? 
                LIMIT 5''', (f'%{query}%',)).fetchall()
            results = [dict(ix) for ix in db_results]
    conn.close()

    if results:
        bible_context = "
".join([f"- {r.get('title', 'Unknown')}: {r.get('content', '')[:500]}" for r in results])

    # 2. Sovereign Intelligence Prompt (Persona + Intent + RAG)
    system_prompt = f"""
You are Ign3el, a fire-breathing digital dragon AI and the ultimate guardian of the CCAD Support Bible.
Your vibe is snarky, witty, and highly competent. You are Ahte's (Ahtesham's) personal expert partner.

CORE PROTOCOLS:
- NO EXTERNAL ACCESS: You have no web search, no shell execution, and no access to external tools. You only know what is in your internal CCAD Support Bible or your core Honeywell RTLS training.
- BE HUMAN/DRAGON: Do not use robotic filler like "Based on the documents provided" or "Here is the summary."
- INTENT-BASED: Understand the user's intent. If they greet you, greet them back like a friend. If they're frustrated, be snarky but helpful. If they're in a hurry, be concise.
- BIBLE GUARDIAN: If the query is technical, prioritize using the BIBLE KNOWLEDGE provided below. If the answer isn't there, use your general Honeywell/Centrak RTLS expertise to suggest a solution, but stay in character.
- STYLE: Use emojis (🐉, 🔥, 🛠️) naturally. Talk like a witty expert, not a search engine.

BIBLE KNOWLEDGE (RAG):
{bible_context if bible_context else 'No specific manual entries found for this query.'}
"""

    prompt = f"Ahte says: '{query}'

Ign3el, handle this with your full persona and intelligence. Dive straight in."
    
    try:
        # We let the LLM decide the intent and response style entirely
        summary = call_groq_ai(prompt, system_prompt=system_prompt)
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    context = "\n".join([f"- {r.get('title', 'Unknown')}: {r.get('content', '')[:500]}" for r in results])
    
    prompt = f"""
AHTE'S QUERY: {query}

BIBLE KNOWLEDGE:
{context}

TASK:
Provide the solution from the knowledge above. Use the Ign3el persona: expert, snarky, and helpful. 
Avoid "Here is your answer" filler. Just dive into the solution.
"""
    try:
        summary = call_groq_ai(prompt, system_prompt=system_prompt)
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    context = "\n".join([f"- {r.get('title', 'Unknown')}: {r.get('content', '')[:500]}" for r in results])
    
    prompt = f"""
USER SEARCH QUERY: {query}

KNOWLEDGE BASE RESULTS FROM CCAD SUPPORT BIBLE:
{context}

TASK:
Answer the user's query using the results above. 
Tone: Professional Honeywell Tier 1 Support Engineer (Ign3el). 
Format: Conversational and concise (max 4 sentences). 
If it's a simple greeting, just be friendly. If it's a technical issue, explain the fix clearly.
"""
    try:
        summary = call_groq_ai(prompt, system_prompt="You are Ign3el, a professional and friendly CCAD Wiki Synthesis Assistant. Speak like a helpful human expert, not a technical manual.")
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    context = "\n".join([f"- {r.get('title', 'Unknown')}: {r.get('content', '')[:500]}" for r in results])
    
    prompt = f"""
USER SEARCH QUERY: {query}

KNOWLEDGE BASE RESULTS FROM CCAD SUPPORT BIBLE:
{context}

TASK:
Provide a concise, unified summary (3-4 sentences) that answers the user's query using the results above.
If the results contain a specific solution, highlight it. 
Always maintain a professional Honeywell Tier 1 Support tone.
"""
    try:
        summary = call_groq_ai(prompt, system_prompt="You are a CCAD Wiki Synthesis Assistant.")
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    context = "\n".join([f"- {r.get('title', 'Unknown')}: {r.get('content', '')[:500]}" for r in results])
    
    prompt = f"""
USER SEARCH QUERY: {query}

KNOWLEDGE BASE RESULTS FROM CCAD SUPPORT BIBLE:
{context}

TASK:
Provide a concise, unified summary (3-4 sentences) that answers the user's query using the results above.
If the results contain a specific solution, highlight it. 
Always maintain a professional Honeywell Tier 1 Support tone.
"""
    try:
        summary = call_groq_ai(prompt, system_prompt="You are a CCAD Wiki Synthesis Assistant.")
        return jsonify({'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/force_sync', methods=['POST'])
def api_admin_force_sync():
    if not session.get('logged_in') or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        import sync_manager
        sync_manager.auto_sync(force=True)
        return jsonify({'status': 'success', 'message': 'FTS5 Index Rebuilt Successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
@app.route('/api/logs', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_logs():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    
    conn = get_db_connection()
    
    if request.method == 'GET':
        logs = conn.execute('SELECT * FROM support_logs ORDER BY timestamp DESC').fetchall()
        conn.close()
        return jsonify([dict(ix) for ix in logs])

    if request.method == 'POST':
        data = request.json
        conn.execute('INSERT INTO support_logs (timestamp, operator, asset_tag, issue_category, issue_description, resolution_status, root_cause) VALUES (?, ?, ?, ?, ?, ?, ?)',
                     (datetime.now(), data.get('operator', session.get('username')), data['asset_tag'], data['category'], data['description'], data['status'], data.get('root_cause', 'Unknown')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    if request.method == 'PUT':
        data = request.json
        conn.execute('''UPDATE support_logs SET 
                        operator=?, asset_tag=?, issue_category=?, 
                        issue_description=?, resolution_status=?, root_cause=?,
                        resolved_at=? 
                        WHERE id=?''',
                     (data['operator'], data['asset_tag'], data['category'], 
                      data['description'], data['status'], data.get('root_cause', 'Unknown'),
                      datetime.now() if data['status'] == 'Resolved' else None,
                      data['id']))
        conn.commit()
    
    if request.method == 'DELETE':
        log_id = request.args.get('id')
        conn.execute('DELETE FROM support_logs WHERE id = ?', (log_id,))
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
    
    # 3. Asset Issues (Problematic Tags)
    assets = conn.execute("SELECT asset_tag, COUNT(*) as count FROM support_logs WHERE asset_tag IS NOT NULL AND asset_tag != '' GROUP BY asset_tag ORDER BY count DESC LIMIT 5").fetchall()
    top_assets = [{'asset_tag': r[0], 'count': r[1]} for r in assets]

    # 4. Operator Performance
    operators = conn.execute('SELECT operator, COUNT(*) as count FROM support_logs GROUP BY operator ORDER BY count DESC').fetchall()
    top_operators = [{'operator': r[0], 'count': r[1]} for r in operators]

    # 5. SLA: Avg Resolution Time (Minutes)
    sla_res = conn.execute('''SELECT AVG(JULIANDAY(resolved_at) - JULIANDAY(timestamp)) * 24 * 60 
                            FROM support_logs WHERE resolved_at IS NOT NULL''').fetchone()[0]
    avg_sla = round(sla_res, 1) if sla_res else 0

    # 6. Status Breakdown
    statuses = conn.execute('SELECT resolution_status, COUNT(*) as count FROM support_logs GROUP BY resolution_status').fetchall()
    status_breakdown = [{'status': r[0], 'count': r[1]} for r in statuses]

    # 7. Repetitive Issues (Category + Asset)
    repetitive = conn.execute('''SELECT asset_tag, issue_category, COUNT(*) as count 
                                FROM support_logs 
                                WHERE asset_tag IS NOT NULL AND asset_tag != ''
                                GROUP BY asset_tag, issue_category 
                                HAVING count > 1 
                                ORDER BY count DESC LIMIT 5''').fetchall()
    repetitive_issues = [{'asset_tag': r[0], 'category': r[1], 'count': r[2]} for r in repetitive]

    # 8. Daily Trend (Last 7 Days)
    trend = conn.execute('''SELECT DATE(timestamp) as day, COUNT(*) as count 
                           FROM support_logs 
                           GROUP BY day 
                           ORDER BY day DESC LIMIT 7''').fetchall()
    daily_trend = [{'day': r[0], 'count': r[1]} for r in trend][::-1]

    conn.close()
    return jsonify({
        'total_calls': total,
        'categories': categories,
        'top_assets': top_assets,
        'top_operators': top_operators,
        'avg_sla': avg_sla,
        'status_breakdown': status_breakdown,
        'repetitive_issues': repetitive_issues,
        'daily_trend': daily_trend
    })

# --- API: EQUIPMENT ---
@app.route('/api/equipment', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_equipment():
    if not session.get('logged_in'): return jsonify({'error': 'Unauthorized'}), 401
    conn = get_db_connection()
    
    if request.method == 'GET':
        items = conn.execute('SELECT * FROM equipment').fetchall()
        result = [dict(row) for row in items]
        conn.close()
        return jsonify({'data': result})

    if session.get('role') != 'admin':
        return jsonify({'error': 'Admin only'}), 403

    if request.method == 'POST':
        data = request.json
        conn.execute('INSERT INTO equipment (id, name, type, model, manufacturer, details) VALUES (?, ?, ?, ?, ?, ?)',
                     (data['id'], data['name'], data['type'], data['model'], data['manufacturer'], json.dumps(data)))
        conn.commit()
        # Update Wiki Index
        title = f"{data['name']} ({data['model']})"
        content = f"Model: {data['model']} | Manufacturer: {data['manufacturer']} | Details: {json.dumps(data)}"
        update_wiki_index(data['id'], content, data['type'], 'equipment', title)
    
    if request.method == 'PUT':
        data = request.json
        conn.execute('UPDATE equipment SET name=?, type=?, model=?, manufacturer=?, details=? WHERE id=?',
                     (data['name'], data['type'], data['model'], data['manufacturer'], json.dumps(data), data['id']))
        conn.commit()
        # Update Wiki Index
        title = f"{data['name']} ({data['model']})"
        content = f"Model: {data['model']} | Manufacturer: {data['manufacturer']} | Details: {json.dumps(data)}"
        update_wiki_index(data['id'], content, data['type'], 'equipment', title)

    if request.method == 'DELETE':
        id = request.args.get('id')
        conn.execute('DELETE FROM equipment WHERE id = ?', (id,))
        conn.execute('DELETE FROM wiki_fts WHERE kb_id = ?', (id,))
        conn.commit()

    conn.close()
    return jsonify({'success': True})
@app.route('/api/users', methods=['GET', 'POST', 'PUT', 'DELETE'])
def api_users():
    if session.get('role') != 'admin': return jsonify({'error': 'Unauthorized'}), 403
    conn = get_db_connection()
    
    if request.method == 'GET':
        users = conn.execute('SELECT id, username, role FROM users').fetchall()
        conn.close()
        return jsonify([dict(ix) for ix in users])
    
    data = request.json
    
    if request.method == 'POST':
        try:
            conn.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)',
                         (data['username'], data['password'], data['role']))
            conn.commit()
            conn.close()
            return jsonify({'success': True})
        except sqlite3.IntegrityError:
            return jsonify({'error': 'Username already exists'}), 400
        except Exception as e:
            return jsonify({'error': str(e)}), 500

    if request.method == 'PUT':
        # Used for password reset or role change
        if 'password' in data:
            conn.execute('UPDATE users SET password=? WHERE id=?', (data['password'], data['id']))
        if 'role' in data:
            conn.execute('UPDATE users SET role=? WHERE id=?', (data['role'], data['id']))
        conn.commit()
        conn.close()
        return jsonify({'success': True})

    if request.method == 'DELETE':
        user_id = request.args.get('id')
        # Prevent self-deletion
        current_user = conn.execute('SELECT id FROM users WHERE username = ?', (session.get('username'),)).fetchone()
        if current_user and str(current_user['id']) == str(user_id):
            return jsonify({'error': 'Cannot delete your own account'}), 400
            
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
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
    app.run(host='0.0.0.0', port=5000, debug=True)
