
import sqlite3
import json
import os

def seed():
    db_path = 'instance/rtls_kb.db'
    json_path = 'full_data.json'
    
    if not os.path.exists(json_path):
        print("Error: full_data.json not found!")
        return

    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    faqs = data.get('faqs', [])
    troubleshooting = data.get('troubleshooting', [])
    equipment = data.get('equipment', []) # New

    print(f"Loaded {len(faqs)} FAQs, {len(troubleshooting)} TS, {len(equipment)} Equipment.")

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Ensure Tables Exist (in case app.py hasn't run or to be safe)
    # KB
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_base (
                 id TEXT PRIMARY KEY,
                 type TEXT,
                 category TEXT,
                 question TEXT,
                 answer TEXT
                 )''')
                 
    # Equipment Table (New)
    c.execute('''CREATE TABLE IF NOT EXISTS equipment (
                 id TEXT PRIMARY KEY,
                 name TEXT,
                 type TEXT,
                 model TEXT,
                 manufacturer TEXT,
                 details TEXT
                 )''')

    # Clear old data
    c.execute('DELETE FROM knowledge_base')
    c.execute('DELETE FROM equipment')
    
    # Insert FAQs
    print("Seeding FAQs...")
    faq_count = 0
    for item in faqs:
        try:
            c.execute('INSERT OR REPLACE INTO knowledge_base (id, type, category, question, answer) VALUES (?, ?, ?, ?, ?)',
                     (item.get('id'), 'faq', item.get('category'), item.get('question'), item.get('answer')))
            faq_count += 1
        except Exception as e:
            print(f"Failed to seed FAQ {item.get('id')}: {e}")
                 
    # Insert Troubleshooting
    print("Seeding Troubleshooting...")
    ts_count = 0
    for item in troubleshooting:
        try:
            json_body = json.dumps(item)
            # Some items might use 'question' instead of 'title' or vice versa
            title = item.get('title') or item.get('question') or 'Untitled'
            c.execute('INSERT OR REPLACE INTO knowledge_base (id, type, category, question, answer) VALUES (?, ?, ?, ?, ?)',
                     (item.get('id'), 'troubleshooting', item.get('category'), title, json_body))
            ts_count += 1
        except Exception as e:
            print(f"Failed to seed TS {item.get('id')}: {e}")
                 
    # Insert Equipment
    print("Seeding Equipment...")
    eq_count = 0
    for item in equipment:
        try:
            json_details = json.dumps(item) 
            c.execute('INSERT OR REPLACE INTO equipment (id, name, type, model, manufacturer, details) VALUES (?, ?, ?, ?, ?, ?)',
                     (item.get('id'), item.get('name'), item.get('type'), item.get('model'), item.get('manufacturer'), json_details))
            eq_count += 1
        except Exception as e:
            print(f"Failed to seed Equipment {item.get('id')}: {e}")

    conn.commit()
    conn.close()
    print(f"Seeding Complete! (FAQs: {faq_count}, TS: {ts_count}, Eq: {eq_count})")


if __name__ == '__main__':
    seed()

