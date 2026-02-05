
import sqlite3
import os

DB_PATH = 'instance/rtls_kb.db'

def consolidate():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Consolidate FAQs
    c.execute("UPDATE knowledge_base SET type = 'faq' WHERE UPPER(type) = 'FAQ'")
    faq_updated = conn.total_changes
    
    # Consolidate Troubleshooting
    c.execute("UPDATE knowledge_base SET type = 'troubleshooting' WHERE UPPER(type) = 'TROUBLESHOOTING'")
    ts_updated = conn.total_changes - faq_updated
    
    conn.commit()
    print(f"Consolidation complete.")
    print(f"Updated {faq_updated} FAQ rows.")
    print(f"Updated {ts_updated} Troubleshooting rows.")
    
    print("\nNew Counts by Type:")
    c.execute("SELECT type, COUNT(*) FROM knowledge_base GROUP BY type")
    for row in c.fetchall():
        print(f"{row[0]}: {row[1]}")
    
    conn.close()

if __name__ == "__main__":
    consolidate()
