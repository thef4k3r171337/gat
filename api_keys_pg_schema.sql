CREATE TABLE api_keys (
            id SERIAL PRIMARY KEY,
            key_id TEXT UNIQUE NOT NULL,
            secret_key TEXT UNIQUE NOT NULL,
            client_name TEXT NOT NULL,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

