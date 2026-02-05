
import sqlite3
import os

DB_PATH = 'instance/rtls_kb.db'

def preprocess_query(query):
    keywords = [k for k in query.replace('"', ' ').replace('*', ' ').replace('(', ' ').replace(')', ' ').split() if len(k) > 1]
    stopwords = {'how', 'to', 'create', 'a', 'with', 'all', 'the', 'is', 'of', 'and', 'for', 'in'}
    filtered = [k for k in keywords if k.lower() not in stopwords]
    if not filtered: return query
    return " OR ".join(filtered)

def test_fix():
    if not os.path.exists(DB_PATH):
        print(f"Error: {DB_PATH} not found")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    query = "How to create a report with all BED tags"
    smart_query = preprocess_query(query)
    print(f"Original: {query}")
    print(f"Preprocessed: {smart_query}")

    try:
        c.execute('''
            SELECT kb_id, title, bm25(wiki_fts) as rank
            FROM wiki_fts 
            WHERE wiki_fts MATCH ? 
            ORDER BY rank 
            LIMIT 5''', (smart_query,))
        results = c.fetchall()
        print(f"\nResults for '{smart_query}':")
        if results:
            for row in results:
                print(f"  [{row[2]:.2f}] {row[0]} | {row[1]}")
        else:
            print("  No results found even with pre-processing.")
    except Exception as e:
        print(f"FTS Error: {e}")

    conn.close()

if __name__ == "__main__":
    test_fix()
