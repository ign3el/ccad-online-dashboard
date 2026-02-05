
import sqlite3
import json
import os
import hashlib

DB_PATH = 'instance/rtls_kb.db'
DATA_FILES = ['kb_data_full.json', 'full_data.json']

def get_file_hash(filepath):
    """Calculate MD5 hash of a file."""
    if not os.path.exists(filepath):
        return None
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def auto_sync(force=False):
    """Check hashes and sync Knowledge Base if changes are detected, or if force is True."""
    if not os.path.exists('instance'):
        os.makedirs('instance')
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Ensure Metadata Table Exists
    c.execute('''CREATE TABLE IF NOT EXISTS sync_metadata (
                 filename TEXT PRIMARY KEY,
                 last_hash TEXT,
                 last_sync DATETIME
                 )''')
    
    # Ensure KB and FTS tables exist
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_base (
                 id TEXT PRIMARY KEY, type TEXT, category TEXT, question TEXT, answer TEXT)''')
    try:
        c.execute('''CREATE VIRTUAL TABLE IF NOT EXISTS wiki_fts USING fts5(
                        kb_id UNINDEXED, content, category, source, title,
                        tokenize = 'porter unicode61')''')
    except: pass

    sync_required = False
    
    for filename in DATA_FILES:
        if not os.path.exists(filename):
            continue
            
        current_hash = get_file_hash(filename)
        c.execute("SELECT last_hash FROM sync_metadata WHERE filename = ?", (filename,))
        row = c.fetchone()
        last_hash = row[0] if row else None
        
        if force or current_hash != last_hash:
            if force:
                print(f"🔄 FORCED Sync: {filename}")
            else:
                print(f"🔄 Change detected in {filename}. Syncing...")
            sync_required = True
            
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            items = []
            if isinstance(data, list): items = data
            elif isinstance(data, dict):
                items.extend(data.get('faqs', []))
                items.extend(data.get('troubleshooting', []))

            for item in items:
                q = item.get('question') or item.get('title') or 'Untitled'
                t = item.get('type', 'faq').lower()
                if 'troubleshooting' in t: t = 'troubleshooting'
                
                ans = item.get('answer')
                if not ans and 'tier1Steps' in item:
                    ans = json.dumps(item)
                
                c.execute('INSERT OR REPLACE INTO knowledge_base (id, type, category, question, answer) VALUES (?, ?, ?, ?, ?)',
                          (item.get('id'), t, item.get('category'), q, ans))
            
            # Update metadata
            c.execute("INSERT OR REPLACE INTO sync_metadata (filename, last_hash, last_sync) VALUES (?, ?, datetime('now'))",
                      (filename, current_hash))
            print(f"  ✅ {filename} synced.")
        else:
            print(f"✨ {filename} is up to date (hash matches).")

    if sync_required:
        print("🔨 Rebuilding Search Index...")
        try:
            c.execute("DELETE FROM wiki_fts")
            c.execute('''
                INSERT INTO wiki_fts (kb_id, content, category, source, title)
                SELECT id, answer, category, type, question FROM knowledge_base
            ''')
            print("  ✅ Search Index Rebuilt.")
        except Exception as e:
            print(f"  ❌ FTS5 Rebuild Error: {e}")
            
    conn.commit()
    conn.close()

if __name__ == "__main__":
    auto_sync()
