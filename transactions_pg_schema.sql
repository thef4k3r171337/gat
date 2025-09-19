CREATE TABLE transactions (
            transaction_id TEXT PRIMARY KEY,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            qr_code_url TEXT,
            pix_code TEXT
        );

