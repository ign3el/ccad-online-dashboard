
import json
import sqlite3
import re

DB_PATH = 'instance/rtls_kb.db'
SHREDS_PATH = 'raw_shreds.json'

CATEGORIES = {
    'Centrak & RTLS Hardware': ['centrak', 'monitors', 'gateways', 'tag', 'star indicator', 'battery', 'antenna', 'pulse'],
    'Medusa & Alerts': ['medusa', 'alert', 'trigger', 'notification', 'rule', 'reset', 'clear alert'],
    'Activate & Reporting': ['activate', 'report', 'schedule', 'template', 'dashboard', 'analytics', 'data archive'],
    'Horizon & Virtual Desktop': ['horizon', 'vdi', 'session', 'client', 'desktop', 'access', 'vmware'],
    'MFA & Authentication': ['mfa', 'authenticate', 'login', 'password', 'active directory', 'ad', 'credential', 'okta', 'duo'],
    'SMTP & Email Integration': ['smtp', 'email', 'mail', 'server', 'relay', 'recipient', 'attachment'],
    'Asset Tagging & Maintenance': ['asset', 'tagging', 'commission', 'decommission', 'floor', 'map', 'workflow']
}

def generate_wiki_entries():
    try:
        with open(SHREDS_PATH, 'r', encoding='utf-8') as f:
            shreds = json.load(f)
    except FileNotFoundError:
        print("Error: raw_shreds.json not found.")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Clear existing wiki entries to avoid duplicates during re-run
    c.execute("DELETE FROM knowledge_base WHERE type='wiki'")
    c.execute("DELETE FROM wiki_fts WHERE source='wiki'")

    print(f"Processing {len(shreds)} pages...")
    wiki_count = 0

    chunk_size = 300
    overlap = 150

    for page in shreds:
        content = page['content'].replace('\n', ' ').strip()
        source = page['source']
        page_num = page['page']
        
        # Sliding Window Logic
        start = 0
        idx = 0
        while start < len(content):
            end = start + chunk_size
            chunk = content[start:end]
            
            if len(chunk.strip()) < 40: 
                start += (chunk_size - overlap)
                continue
            
            # Identify Category & Keywords
            found_cat = "General Knowledge"
            prefix = ""
            for cat, keywords in CATEGORIES.items():
                matched = [kw for kw in keywords if kw in chunk.lower()]
                if matched:
                    found_cat = cat
                    prefix = matched[0].capitalize() + ": "
                    break
            
            # Generate Synthetic Title/Question
            words = chunk.strip().split()
            title = prefix + " ".join(words[:6]) + "..."
            
            item_id = f"WIKI-{re.sub(r'[^A-Z0-9]', '', source.upper())[:5]}-{page_num}-{idx}"
            
            # Insert into knowledge_base
            c.execute('INSERT OR REPLACE INTO knowledge_base (id, type, category, question, answer) VALUES (?, ?, ?, ?, ?)',
                      (item_id, 'wiki', found_cat, title, chunk.strip()))
            
            # Insert into wiki_fts
            c.execute('INSERT INTO wiki_fts (kb_id, content, category, source, title) VALUES (?, ?, ?, ?, ?)',
                      (item_id, chunk.strip(), found_cat, 'wiki', title))
            
            wiki_count += 1
            idx += 1
            start += (chunk_size - overlap)

    conn.commit()
    conn.close()
    print(f"Success! Generated and indexed {wiki_count} granular Wiki entries.")

if __name__ == "__main__":
    generate_wiki_entries()
