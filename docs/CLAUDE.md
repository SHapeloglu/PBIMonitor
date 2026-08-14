# CLAUDE.md — PBIMonitor Proje Rehberi

Bu dosya yeni bir chat oturumuna taşındığında Claude un projeyi sıfırdan anlayabilmesi için
hazırlanmıştır. Diğer MD dosyalarıyla birlikte kullanılır.

---

## Proje Kimliği

PBIMonitor — Power BI izleme SaaS platformu.
Canlı URL: http://95.111.242.96:8003
Sunucu: Contabo VPS
Klasör: /root/pbimonitor_final/

---

## Teknoloji Yığını

Backend: Flask + PyMySQL + MySQL 8.0
Frontend: Jinja2 + Vanilla JS
Bildirim: WhatsApp Business API + SMTP
Şifreleme: Fernet (cryptography)
Altyapı: Docker + docker-compose
Port: 8003

---

## Docker Yapısı

pbimonitor-db (MySQL 8.0)
pbimonitor-web (Flask/Gunicorn, port 8003)
pbimonitor-scheduler (Python daemon, 30 dakika)

Network sorunu: web + scheduler manuel bağlantı gerekli
  docker network connect pbimonitor_pbimonitor-net pbimonitor-web
  docker network connect pbimonitor_pbimonitor-net pbimonitor-scheduler
  docker restart pbimonitor-web pbimonitor-scheduler

---

## Dosya Yapısı

app.py, auth.py, db.py, pbi.py, monitor.py, scheduler.py, crypto_utils.py
requirements.txt, docker-compose.yml, .env (gitignore da)
templates/ klasörü

---

## .env İçeriği

DB_HOST=db
DB_PORT=3306
DB_NAME=pbimonitor
DB_USER=pbimonitor
DB_PASSWORD=BirNisan82
FLASK_SECRET=pbimonitor-gizli-anahtar-2026
ENCRYPTION_KEY=<fernet_key>

ENCRYPTION_KEY üret:
  python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

---

## Power BI Konfigurasyonu

CLIENT_ID: 14d82eec-204b-4c2f-b7e8-296a70dab67e
SCOPE: Dataset.Read.All Workspace.Read.All Gateway.Read.All offline_access
AUTH_ENDPOINT: organizations (Multitenant)

Azure Portal beklemede: App Registration Multitenant yapılmadı.

---

## Deploy Komutları

cd /root/pbimonitor_final
docker compose up -d --build
docker network connect pbimonitor_pbimonitor-net pbimonitor-web
docker network connect pbimonitor_pbimonitor-net pbimonitor-scheduler
docker restart pbimonitor-web pbimonitor-scheduler
docker logs pbimonitor-web --tail 20
