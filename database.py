import sqlite3

DATABASE = 'transactions.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            qr_code_url TEXT,
            pix_code TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_transaction(transaction_id, amount, description, status, qr_code_url, pix_code):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO transactions (transaction_id, amount, description, status, qr_code_url, pix_code) VALUES (?, ?, ?, ?, ?, ?)",
                   (transaction_id, amount, description, status, qr_code_url, pix_code))
    conn.commit()
    conn.close()

def update_transaction_status(transaction_id, status):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("UPDATE transactions SET status = ? WHERE transaction_id = ?", (status, transaction_id))
    conn.commit()
    conn.close()

def get_transaction(transaction_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,))
    transaction = cursor.fetchone()
    conn.close()
    if transaction:
        return {
            'transaction_id': transaction[0],
            'amount': transaction[1],
            'description': transaction[2],
            'status': transaction[3],
            'qr_code_url': transaction[4],
            'pix_code': transaction[5]
        }
    return None


