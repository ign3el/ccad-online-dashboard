
import sqlite3
import os

DB_PATH = 'instance/rtls_kb.db'

def test_search():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    queries = [
        "bed",
        "report",
        "report bed",
        "report OR bed",
        "How to create a report with all BED tags"
    ]

    for q in queries:
        print(f"\n--- Testing MATCH for: '{q}' ---")
        try:
            c.execute("SELECT kb_id, title FROM wiki_fts WHERE wiki_fts MATCH ? LIMIT 3", (q,))
            results = c.fetchall()
            if results:
                for row in results:
                    print(f"  Found: {row[0]} | {row[1]}")
            else:
                print("  No results.")
        except Exception as e:
            print(f"  FTS Error: {e}")

    conn.close()

if __name__ == "__main__":
    test_search()
