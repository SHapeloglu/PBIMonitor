import re, sys

def patch_file(path, replacements):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for old, new, label in replacements:
        count = content.count(old)
        if count == 0:
            print(f"HATA [{path}] anchor bulunamadi: {label}")
            sys.exit(1)
        if count > 1:
            print(f"HATA [{path}] anchor {count} kez bulundu: {label}")
            sys.exit(1)
        content = content.replace(old, new)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"OK: {path} yamalandi ({len(replacements)} degisiklik)")

pbi_replacements = [
    (
        "from db import get_db\n",
        "from db import get_db\nfrom crypto_utils import encrypt, decrypt\n",
        "import ekle"
    ),
    (
        "    if datetime.now(timezone.utc).timestamp() < conn['token_expires_at'] - 60:\n"
        "        return conn['token']\n",
        "    if datetime.now(timezone.utc).timestamp() < conn['token_expires_at'] - 60:\n"
        "        return decrypt(conn['token'])\n",
        "token_yukle decrypt"
    ),
    (
        "    if conn.get('refresh_token'):\n"
        "        yeni = token_yenile(user_id, conn['refresh_token'])\n",
        "    if conn.get('refresh_token'):\n"
        "        yeni = token_yenile(user_id, decrypt(conn['refresh_token']))\n",
        "refresh_token decrypt"
    ),
    (
        "    db = get_db()\n"
        "    cursor = db.cursor()\n"
        "    cursor.execute(\"\"\"\n"
        "        INSERT INTO pbi_connections (user_id, tenant_id, token, token_expires_at, refresh_token)\n"
        "        VALUES (%s, %s, %s, %s, %s)\n"
        "        ON DUPLICATE KEY UPDATE token=%s, token_expires_at=%s, refresh_token=%s, tenant_id=%s\n"
        "    \"\"\", (user_id, gercek_tenant_id, access_token, expires_at, refresh_token, access_token, expires_at, refresh_token, gercek_tenant_id))\n",
        "    enc_token = encrypt(access_token)\n"
        "    enc_refresh = encrypt(refresh_token)\n"
        "    db = get_db()\n"
        "    cursor = db.cursor()\n"
        "    cursor.execute(\"\"\"\n"
        "        INSERT INTO pbi_connections (user_id, tenant_id, token, token_expires_at, refresh_token)\n"
        "        VALUES (%s, %s, %s, %s, %s)\n"
        "        ON DUPLICATE KEY UPDATE token=%s, token_expires_at=%s, refresh_token=%s, tenant_id=%s\n"
        "    \"\"\", (user_id, gercek_tenant_id, enc_token, expires_at, enc_refresh, enc_token, expires_at, enc_refresh, gercek_tenant_id))\n",
        "token_kaydet encrypt"
    ),
]

monitor_replacements = [
    (
        "from db import get_db\n",
        "from db import get_db\nfrom crypto_utils import decrypt\n",
        "import ekle"
    ),
    (
        "        \"password\": user.get(\"smtp_password\") or \"\"\n",
        "        \"password\": decrypt(user.get(\"smtp_password\")) or \"\"\n",
        "smtp_password decrypt"
    ),
    (
        "                    user.get(\"gateway_wa_token\"),\n",
        "                    decrypt(user.get(\"gateway_wa_token\")),\n",
        "gateway_wa_token decrypt"
    ),
]

def patch_wa_token_calls(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    old1 = 'whatsapp_gonder(mesaj, config["phone_number_id"], config["wa_token"], config["alici_whatsapp"])'
    new1 = 'whatsapp_gonder(mesaj, config["phone_number_id"], decrypt(config["wa_token"]), config["alici_whatsapp"])'
    old2 = 'whatsapp_gonder(mesaj_ardisik, config["phone_number_id"], config["wa_token"], config["alici_whatsapp"])'
    new2 = 'whatsapp_gonder(mesaj_ardisik, config["phone_number_id"], decrypt(config["wa_token"]), config["alici_whatsapp"])'
    n1 = content.count(old1)
    n2 = content.count(old2)
    if n1 == 0 and n2 == 0:
        print(f"HATA [{path}] wa_token cagrisi bulunamadi")
        sys.exit(1)
    content = content.replace(old1, new1)
    content = content.replace(old2, new2)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"OK: {path} icinde {n1+n2} wa_token cagrisi decrypt ile sarildi")

app_replacements = [
    (
        "from db import get_db\n",
        "from db import get_db\nfrom crypto_utils import encrypt, decrypt\n",
        "import ekle"
    ),
    (
        "    \"\"\", (data.get('smtp_host'), data.get('smtp_port', 587), data.get('smtp_user'), data.get('smtp_password'), user_id))\n",
        "    \"\"\", (data.get('smtp_host'), data.get('smtp_port', 587), data.get('smtp_user'), encrypt(data.get('smtp_password')), user_id))\n",
        "smtp_password encrypt"
    ),
    (
        "    smtp = {\"host\": user['smtp_host'], \"port\": user['smtp_port'] or 587, \"user\": user['smtp_user'], \"password\": user['smtp_password'] or ''}\n",
        "    smtp = {\"host\": user['smtp_host'], \"port\": user['smtp_port'] or 587, \"user\": user['smtp_user'], \"password\": decrypt(user['smtp_password']) or ''}\n",
        "smtp_password decrypt"
    ),
    (
        "        data.get('phone_number_id', ''), data.get('wa_token', ''), data.get('ust_uste_hata_esik', 3), data.get('beklenen_refresh_saat', 24), data.get('sure_sapma_yuzdesi', 150),\n",
        "        data.get('phone_number_id', ''), encrypt(data.get('wa_token', '')), data.get('ust_uste_hata_esik', 3), data.get('beklenen_refresh_saat', 24), data.get('sure_sapma_yuzdesi', 150),\n",
        "wa_token INSERT encrypt"
    ),
    (
        "        data.get('phone_number_id', ''), data.get('wa_token', ''), data.get('ust_uste_hata_esik', 3), data.get('beklenen_refresh_saat', 24), data.get('sure_sapma_yuzdesi', 150)\n"
        "    ))",
        "        data.get('phone_number_id', ''), encrypt(data.get('wa_token', '')), data.get('ust_uste_hata_esik', 3), data.get('beklenen_refresh_saat', 24), data.get('sure_sapma_yuzdesi', 150)\n"
        "    ))",
        "wa_token UPDATE encrypt"
    ),
    (
        "        data.get('gateway_phone_number_id', ''), data.get('gateway_wa_token', ''),\n",
        "        data.get('gateway_phone_number_id', ''), encrypt(data.get('gateway_wa_token', '')),\n",
        "gateway_wa_token encrypt"
    ),
]

patch_file("pbi.py", pbi_replacements)
patch_file("monitor.py", monitor_replacements)
patch_wa_token_calls("monitor.py")
patch_file("app.py", app_replacements)

import subprocess
r = subprocess.run(["python3", "-m", "py_compile", "pbi.py", "monitor.py", "app.py"], capture_output=True, text=True)
if r.returncode != 0:
    print("SOZDIZIMI HATASI:"); print(r.stderr); sys.exit(1)
print("\nTUM DOSYALAR YAMALANDI VE SOZDIZIMI GECERLI.")
