
import sqlite3
import json
import os
import re

DB_PATH = 'instance/rtls_kb.db'
DATA_FILES = ['kb_data_full.json', 'full_data.json', 'raw_shreds.json']

def safe_sync():
    if not os.path.exists('instance'):
        os.makedirs('instance')
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Ensure Tables Exist
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_base (
                 id TEXT PRIMARY KEY, type TEXT, category TEXT, question TEXT, answer TEXT)''')
    
    # 2. Sync from JSON files
    for filename in DATA_FILES:
        if not os.path.exists(filename):
            continue
            
        print(f"Processing {filename}...")
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Handle different JSON structures
        items = []
        if isinstance(data, list):
            items = data
        elif isinstance(data, dict):
            # Combine faqs and troubleshooting if they exist
            items.extend(data.get('faqs', []))
            items.extend(data.get('troubleshooting', []))
            
        count = 0
        for item in items:
            # Normalize type and handle field naming differences
            q = item.get('question') or item.get('title') or 'Untitled'
            t = item.get('type', 'faq').lower()
            if 'troubleshooting' in t: t = 'troubleshooting'
            
            # For TS, we store the whole object as JSON in the 'answer' field if it has steps
            ans = item.get('answer')
            if not ans and 'tier1Steps' in item:
                ans = json.dumps(item)
            
            c.execute('INSERT OR REPLACE INTO knowledge_base (id, type, category, question, answer) VALUES (?, ?, ?, ?, ?)',
                      (item.get('id'), t, item.get('category'), q, ans))
            count += 1
        print(f"  Merged {count} entries from {filename}")

    # 3. Special Handling for Shreds (Wiki) if bulk_seed_wiki logic is needed
    # (Optional: User can just run bulk_seed_wiki.py after this if they want granular chunks)
    
    # 4. Rebuild FTS5 Index (Safe for production)
    print("Rebuilding Search Index (FTS5)...")
    try:
        c.execute("DELETE FROM wiki_fts") # Clear index table only
        c.execute('''
            INSERT INTO wiki_fts (kb_id, content, category, source, title)
            SELECT id, answer, category, type, question FROM knowledge_base
        ''')
        print("  Search Index Rebuilt Successfully.")
    except Exception as e:
        print(f"  FTS5 Sync Error: {e}")

    conn.commit()
    conn.close()
    print("\nSAFE SYNC COMPLETE. Your users and logs were not affected.")

if __name__ == "__main__":
    safe_sync()
