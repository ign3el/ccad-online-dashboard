
import sqlite3
import json
import os

DB_PATH = 'instance/rtls_kb.db'
JSON_PATH = 'kb_data_full.json'

def seed_db():
    if not os.path.exists('instance'):
        os.makedirs('instance')
        
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE,
                 password TEXT,
                 role TEXT
                 )''')
    
    # Knowledge Base Table
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_base (
                 id TEXT PRIMARY KEY,
                 type TEXT,
                 category TEXT,
                 question TEXT,
                 answer TEXT
                 )''')
    
    # Create Logs Table (if not exists)
    c.execute('''CREATE TABLE IF NOT EXISTS support_logs (
                 id INTEGER PRIMARY KEY AUTOINCREMENT,
                 timestamp DATETIME,
                 operator TEXT,
                 asset_tag TEXT,
                 issue_category TEXT,
                 issue_description TEXT,
                 resolution_status TEXT,
                 root_cause TEXT
                 )''')

    # Load Data
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        count = 0
        for item in data:
            try:
                c.execute('INSERT OR IGNORE INTO knowledge_base (id, type, category, question, answer) VALUES (?, ?, ?, ?, ?)',
                          (item['id'], item['type'], item['category'], item['question'], item['answer']))
                count += 1
            except Exception as e:
                print(f"Skipping {item['id']}: {e}")
                
        conn.commit()
        print(f"Seeded {count} entries into {DB_PATH}")
        
    except FileNotFoundError:
        print(f"Could not find {JSON_PATH}")
    finally:
        conn.close()
    
    # Run Automated Sync (Hash-based)
    try:
        import sync_manager
        sync_manager.auto_sync()
    except Exception as e:
        print(f"Auto-sync failed: {e}")

if __name__ == "__main__":
    seed_db()
