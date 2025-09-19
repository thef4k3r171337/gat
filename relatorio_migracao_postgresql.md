# Relatório de Migração para PostgreSQL

## Introdução

Este relatório detalha o processo de migração de um banco de dados SQLite existente para um ambiente PostgreSQL. O objetivo foi converter a estrutura do banco de dados e transferir os dados existentes, garantindo a integridade e funcionalidade no novo sistema de gerenciamento de banco de dados.

## Bancos de Dados Originais (SQLite)

O banco de dados original `transactions.db` continha as seguintes tabelas:

### Tabela: `transactions`

```sql
CREATE TABLE transactions (
            transaction_id TEXT PRIMARY KEY,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            qr_code_url TEXT,
            pix_code TEXT
        );
```

### Tabela: `api_keys`

```sql
CREATE TABLE api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_id TEXT UNIQUE NOT NULL,
            secret_key TEXT UNIQUE NOT NULL,
            client_name TEXT NOT NULL,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
```

## Migração para PostgreSQL

### 1. Adaptação do Esquema

Os esquemas das tabelas foram adaptados para a sintaxe do PostgreSQL. As principais alterações incluíram:

*   `INTEGER PRIMARY KEY AUTOINCREMENT` foi substituído por `SERIAL PRIMARY KEY` para colunas de auto-incremento.
*   `BOOLEAN DEFAULT 1` foi substituído por `BOOLEAN DEFAULT TRUE`.

#### Esquema PostgreSQL para `transactions`

```sql
CREATE TABLE transactions (
            transaction_id TEXT PRIMARY KEY,
            amount REAL NOT NULL,
            description TEXT NOT NULL,
            status TEXT NOT NULL,
            qr_code_url TEXT,
            pix_code TEXT
        );
```

#### Esquema PostgreSQL para `api_keys`

```sql
CREATE TABLE api_keys (
            id SERIAL PRIMARY KEY,
            key_id TEXT UNIQUE NOT NULL,
            secret_key TEXT UNIQUE NOT NULL,
            client_name TEXT NOT NULL,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
```

### 2. Extração e Importação de Dados

Os dados das tabelas `transactions` e `api_keys` foram extraídos do SQLite para arquivos CSV (`transactions_data.csv` e `api_keys_data.csv`). Em seguida, um script Python (`import_data.py`) foi criado para importar esses dados para as tabelas recém-criadas no PostgreSQL.

#### Script de Importação de Dados (`import_data.py`)

```python
import csv
import psycopg2

# Configurações do PostgreSQL
DB_HOST = "localhost"
DB_NAME = "pix_db"
DB_USER = "postgres"
DB_PASSWORD = "postgres"

def import_csv_to_postgres(csv_file, table_name):
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASSWORD)
        cur = conn.cursor()

        with open(csv_file, 'r') as f:
            reader = csv.reader(f)
            header = next(reader)  # Skip header row
            
            # Construct the INSERT statement dynamically
            columns = ", ".join(header)
            placeholders = ", ".join([f"%s" for _ in header])
            insert_sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

            for row in reader:
                cur.execute(insert_sql, row)
        
        conn.commit()
        cur.close()
        conn.close()
        print(f"Dados de {csv_file} importados com sucesso para a tabela {table_name}.")

    except Exception as e:
        print(f"Erro ao importar dados de {csv_file}: {e}")

if __name__ == "__main__":
    import_csv_to_postgres("transactions_data.csv", "transactions")
    import_csv_to_postgres("api_keys_data.csv", "api_keys")
```

### 3. Validação da Migração

Após a importação, a contagem de registros em cada tabela no PostgreSQL foi verificada para garantir que todos os dados foram transferidos corretamente.

*   **Tabela `transactions`**: 6 registros
*   **Tabela `api_keys`**: 1 registro

Essas contagens correspondem aos dados extraídos do banco de dados SQLite original.

## Conclusão

O processo de migração do banco de dados SQLite para PostgreSQL foi concluído com sucesso. A estrutura do banco de dados foi adaptada e os dados foram transferidos e validados, garantindo que o novo ambiente PostgreSQL esteja pronto para uso.

## Arquivos Gerados

*   `transactions_pg_schema.sql`: Esquema da tabela `transactions` para PostgreSQL.
*   `api_keys_pg_schema.sql`: Esquema da tabela `api_keys` para PostgreSQL.
*   `transactions_data.csv`: Dados da tabela `transactions` em formato CSV.
*   `api_keys_data.csv`: Dados da tabela `api_keys` em formato CSV.
*   `import_data.py`: Script Python para importar dados CSV para PostgreSQL.
*   `relatorio_migracao_postgresql.md`: Este relatório.


