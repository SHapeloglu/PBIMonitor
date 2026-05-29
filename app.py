from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from auth import auth
from db import get_db
from pbi import token_gecerli_mi, token_yukle, token_kaydet, device_code_baslat, device_code_tamamla, datasetleri_getir
from monitor import dataset_kontrol
import json
import pymysql.cursors
app = Flask(__name__)
app.secret_key = "pbimonitor-gizli-anahtar-2026"

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
        token_kaydet(session['user_id'], result['access_token'], result['expires_in'])
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
    cursor = db.cursor(pymysql.cursors.DictCursor)
    
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
    cursor = db.cursor(pymysql.cursors.DictCursor)
    
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
            (dataset_id, hata_whatsapp, hata_mail, basarili_mail, alici_whatsapp, alici_mail, normal_sure, phone_number_id, wa_token)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            hata_whatsapp=%s, hata_mail=%s, basarili_mail=%s,
            alici_whatsapp=%s, alici_mail=%s, normal_sure=%s,
            phone_number_id=%s, wa_token=%s
    """, (
        dataset_id,
        data.get('hata_whatsapp', False),
        data.get('hata_mail', False),
        data.get('basarili_mail', False),
        data.get('alici_whatsapp', ''),
        data.get('alici_mail', ''),
        data.get('normal_sure', 300),
        data.get('phone_number_id', ''),
        data.get('wa_token', ''),
        data.get('hata_whatsapp', False),
        data.get('hata_mail', False),
        data.get('basarili_mail', False),
        data.get('alici_whatsapp', ''),
        data.get('alici_mail', ''),
        data.get('normal_sure', 300),
        data.get('phone_number_id', ''),
        data.get('wa_token', '')
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
    cursor = db.cursor(pymysql.cursors.DictCursor)
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

if __name__ == '__main__':
    app.run(debug=True)