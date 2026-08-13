from db import get_db
from crypto_utils import encrypt, decrypt

def migrate_column(cursor, table, id_col, col):
    cursor.execute(f"SELECT {id_col}, {col} FROM {table} WHERE {col} IS NOT NULL AND {col} != ''")
    rows = cursor.fetchall()
    updated = 0
    for row in rows:
        raw_val = row[col]
        plain = decrypt(raw_val)
        if plain == raw_val:
            cursor.execute(f"UPDATE {table} SET {col} = %s WHERE {id_col} = %s", (encrypt(plain), row[id_col]))
            updated += 1
    return updated, len(rows)

db = get_db()
cursor = db.cursor()
for table, id_col, col in [
    ("pbi_connections", "id", "token"),
    ("pbi_connections", "id", "refresh_token"),
    ("users", "id", "smtp_password"),
    ("users", "id", "gateway_wa_token"),
    ("dataset_config", "id", "wa_token"),
]:
    u, t = migrate_column(cursor, table, id_col, col)
    print(f"{table}.{col}: {u}/{t} sifrelendi")
db.commit()
cursor.close()
db.close()
print("TAMAMLANDI.")
