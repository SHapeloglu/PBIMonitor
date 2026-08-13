import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from auth import auth
from db import get_db
from crypto_utils import encrypt, decrypt
from pbi import token_gecerli_mi, token_yukle, token_kaydet, device_code_baslat, device_code_tamamla, datasetleri_getir, gatewayleri_getir
from monitor import dataset_kontrol, gateway_kontrol

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "pbimonitor-gizli-anahtar-2026")

app.register_blueprint(auth)

def giris_gerekli(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated

@app.route('/')
@giris_gerekli
def dashboard():
    return render_template('dashboard.html', email=session.get('email'))

@app.route('/api/pbi/baglant_baslat')
@giris_gerekli
def pbi_baglanti_baslat():
    result = device_code_baslat()
    return jsonify(result)

@app.route('/api/pbi/baglanti_tamamla', methods=['POST'])
@giris_gerekli
def pbi_baglanti_tamamla():
    device_code = request.json.get('device_code')
    result = device_code_tamamla(device_code)
    if 'access_token' in result:
        token_kaydet(session['user_id'], result['access_token'], result['expires_in'], result.get('refresh_token'))
        return jsonify({"status": "ok"})
    return jsonify({"status": "hata", "mesaj": result.get("error_description", "Bilinmeyen hata")}), 400

@app.route('/api/pbi/durum')
@giris_gerekli
def pbi_durum():
    return jsonify({"bagli": token_gecerli_mi(session['user_id'])})

@app.route('/api/datasets')
@giris_gerekli
def api_datasets():
    if not token_gecerli_mi(session['user_id']):
        return jsonify({"error": "token_yok"}), 401
    token = token_yukle(session['user_id'])

    db = get_db()
    cursor = db.cursor()
    datasets = datasetleri_getir(token)

    for ds in datasets:
        cursor.execute("""
            SELECT dc.* FROM datasets d
            LEFT JOIN dataset_config dc ON dc.dataset_id = d.id
            WHERE d.user_id = %s AND d.pbi_dataset_id = %s
        """, (session['user_id'], ds['id']))
        config = cursor.fetchone()
        ds['ayarlar'] = config or {}

    cursor.close()
    db.close()
    return jsonify(datasets)

@app.route('/api/ayarlar', methods=['POST'])
@giris_gerekli
def ayarlar_kaydet():
    data = request.json
    user_id = session['user_id']
    pbi_dataset_id = data.get('dataset_id')

    db = get_db()
    cursor = db.cursor()

    cursor.execute("""
        SELECT id FROM datasets
        WHERE user_id = %s AND pbi_dataset_id = %s
    """, (user_id, pbi_dataset_id))
    dataset = cursor.fetchone()

    if not dataset:
        cursor.execute("""
            INSERT INTO datasets (user_id, pbi_dataset_id, workspace_id, workspace_name, name)
            VALUES (%s, %s, %s, %s, %s)
        """, (user_id, pbi_dataset_id, data.get('workspace_id', ''), data.get('workspace', ''), data.get('name', '')))
        db.commit()
        dataset_id = cursor.lastrowid
    else:
        dataset_id = dataset['id']

    cursor.execute("""
        INSERT INTO dataset_config
            (dataset_id, hata_whatsapp, hata_mail, basarili_mail, alici_whatsapp, alici_mail, normal_sure, phone_number_id, wa_token, ust_uste_hata_esik, beklenen_refresh_saat, sure_sapma_yuzdesi)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            hata_whatsapp=%s, hata_mail=%s, basarili_mail=%s,
            alici_whatsapp=%s, alici_mail=%s, normal_sure=%s,
            phone_number_id=%s, wa_token=%s, ust_uste_hata_esik=%s, beklenen_refresh_saat=%s, sure_sapma_yuzdesi=%s
    """, (
        dataset_id,
        data.get('hata_whatsapp', False), data.get('hata_mail', False), data.get('basarili_mail', False),
        data.get('alici_whatsapp', ''), data.get('alici_mail', ''), data.get('normal_sure', 300),
        data.get('phone_number_id', ''), encrypt(data.get('wa_token', '')), data.get('ust_uste_hata_esik', 3), data.get('beklenen_refresh_saat', 24), data.get('sure_sapma_yuzdesi', 150),
        data.get('hata_whatsapp', False), data.get('hata_mail', False), data.get('basarili_mail', False),
        data.get('alici_whatsapp', ''), data.get('alici_mail', ''), data.get('normal_sure', 300),
        data.get('phone_number_id', ''), encrypt(data.get('wa_token', '')), data.get('ust_uste_hata_esik', 3), data.get('beklenen_refresh_saat', 24), data.get('sure_sapma_yuzdesi', 150)
    ))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"status": "ok"})

@app.route('/api/kontrol')
@giris_gerekli
def manuel_kontrol():
    if not token_gecerli_mi(session['user_id']):
        return jsonify({"error": "token_yok"}), 401
    token = token_yukle(session['user_id'])
    datasets = datasetleri_getir(token)
    sonuclar = dataset_kontrol(session['user_id'], datasets)
    return jsonify(sonuclar)

@app.route('/api/alarm_log')
@giris_gerekli
def alarm_log():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT al.*, d.name as dataset_name
        FROM alarm_log al
        JOIN datasets d ON d.id = al.dataset_id
        WHERE d.user_id = %s
        ORDER BY al.created_at DESC
        LIMIT 50
    """, (session['user_id'],))
    logs = cursor.fetchall()
    cursor.close()
    db.close()
    for log in logs:
        log['created_at'] = str(log['created_at'])
    return jsonify(logs)

@app.route('/alarm-log')
@giris_gerekli
def alarm_log_sayfasi():
    return render_template('alarm_log.html', email=session.get('email'))

@app.route('/ayarlar')
@giris_gerekli
def ayarlar_sayfasi():
    return render_template('ayarlar.html', email=session.get('email'))

@app.route('/api/ayarlar/smtp', methods=['GET', 'POST'])
@giris_gerekli
def smtp_ayarlari():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()

    if request.method == 'GET':
        cursor.execute("SELECT smtp_host, smtp_port, smtp_user FROM users WHERE id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        db.close()
        return jsonify(row or {})

    data = request.json
    cursor.execute("""
        UPDATE users SET smtp_host=%s, smtp_port=%s, smtp_user=%s, smtp_password=%s WHERE id=%s
    """, (data.get('smtp_host'), data.get('smtp_port', 587), data.get('smtp_user'), encrypt(data.get('smtp_password')), user_id))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"status": "ok"})

@app.route('/api/ayarlar/smtp/test', methods=['POST'])
@giris_gerekli
def smtp_test():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT email, smtp_host, smtp_port, smtp_user, smtp_password FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    db.close()

    if not user or not user.get('smtp_host'):
        return jsonify({"status": "hata", "mesaj": "Once SMTP ayarlarini kaydedin."})

    from monitor import mail_gonder
    smtp = {"host": user['smtp_host'], "port": user['smtp_port'] or 587, "user": user['smtp_user'], "password": decrypt(user['smtp_password']) or ''}
    basarili = mail_gonder("PBI Monitor - Test Maili", "Bu bir test mailidir. SMTP ayarlariniz calisıyor.", user['email'], smtp)
    if basarili:
        return jsonify({"status": "ok", "mesaj": f"Test maili {user['email']} adresine gonderildi."})
    return jsonify({"status": "hata", "mesaj": "Mail gonderilemedi. SMTP bilgilerini kontrol edin."})

@app.route('/gateway')
@giris_gerekli
def gateway_sayfasi():
    return render_template('gateway.html', email=session.get('email'))

@app.route('/api/gateways')
@giris_gerekli
def api_gateways():
    if not token_gecerli_mi(session['user_id']):
        return jsonify({"error": "token_yok"}), 401
    token = token_yukle(session['user_id'])
    gateways = gatewayleri_getir(token)
    return jsonify(gateways)

@app.route('/api/gateway_kontrol')
@giris_gerekli
def api_gateway_kontrol():
    if not token_gecerli_mi(session['user_id']):
        return jsonify({"error": "token_yok"}), 401
    token = token_yukle(session['user_id'])
    gateways = gatewayleri_getir(token)
    sonuclar = gateway_kontrol(session['user_id'], gateways)
    return jsonify(sonuclar)

@app.route('/api/gateway_log')
@giris_gerekli
def api_gateway_log():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("""
        SELECT * FROM gateway_status_log
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 50
    """, (session['user_id'],))
    logs = cursor.fetchall()
    cursor.close()
    db.close()
    for log in logs:
        log['created_at'] = str(log['created_at'])
    return jsonify(logs)

@app.route('/api/ayarlar/gateway', methods=['GET', 'POST'])
@giris_gerekli
def gateway_ayarlari():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()

    if request.method == 'GET':
        cursor.execute("""
            SELECT gateway_alarm_mail, gateway_alarm_whatsapp, gateway_alici_mail,
                   gateway_alici_whatsapp, gateway_phone_number_id
            FROM users WHERE id = %s
        """, (user_id,))
        row = cursor.fetchone()
        cursor.close()
        db.close()
        return jsonify(row or {})

    data = request.json
    cursor.execute("""
        UPDATE users SET
            gateway_alarm_mail=%s, gateway_alarm_whatsapp=%s,
            gateway_alici_mail=%s, gateway_alici_whatsapp=%s,
            gateway_phone_number_id=%s, gateway_wa_token=%s
        WHERE id=%s
    """, (
        data.get('gateway_alarm_mail', False), data.get('gateway_alarm_whatsapp', False),
        data.get('gateway_alici_mail', ''), data.get('gateway_alici_whatsapp', ''),
        data.get('gateway_phone_number_id', ''), encrypt(data.get('gateway_wa_token', '')),
        user_id
    ))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"status": "ok"})

@app.route('/api/pbi/baglanti_sifirla', methods=['POST'])
@giris_gerekli
def pbi_baglanti_sifirla():
    user_id = session['user_id']
    db = get_db()
    cursor = db.cursor()
    cursor.execute("DELETE FROM pbi_connections WHERE user_id = %s", (user_id,))
    db.commit()
    cursor.close()
    db.close()
    return jsonify({"status": "ok"})


