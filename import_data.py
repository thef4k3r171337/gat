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


