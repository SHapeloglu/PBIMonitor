# Claude Talimatlari

## Proje
PBI Monitor - Power BI izleme SaaS platformu

## Stack
- Backend: Flask (Python 3.13)
- DB: MySQL 8.0 (PyMySQL) - Docker container
- Hosting: Contabo VPS, Docker
- Frontend: Jinja2 + Vanilla JS
- Port: 8003

## Kritik Kurallar
- cursor(dictionary=True) KULLANMA - PyMySQL desteklemiyor
- db.py'de DictCursor zaten tanimli, cursor() yeterli
- Emoji iceren string DB'ye yazilirken sorun cikarabilir, kullanma
- Sifreleri asla koda yazma, .env kullan
- Docker deploy: docker-compose up -d --build

## Deploy
1. VSCode'da degisiklik yap
2. git push origin main
3. Contabo: git pull origin main && docker-compose up -d --build

## Dosya Yapisi
pbimonitor/
├── app.py           Flask routes
├── auth.py          Giris/kayit
├── db.py            MySQL baglantisi (env variable)
├── pbi.py           Power BI API + refresh token
├── monitor.py       Alarm ve kontrol (smtp_yukle ile kullanici bazli SMTP)
├── scheduler.py     30 dk'da bir otomatik kontrol (ayri container)
├── init.sql         DB ilk kurulum (docker-compose ile otomatik)
├── Dockerfile
├── docker-compose.yml  3 servis: db, web, scheduler
├── .env             (gitignore'da, kopyalanmaz)
├── .env.example     (ornek, GitHub'da)
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── alarm_log.html   Alarm gecmisi sayfasi
│   ├── ayarlar.html     SMTP + PBI baglanti + Gateway alarm ayarlari
│   ├── gateway.html     Gateway/datasource durum izleme sayfasi
│   ├── login.html
│   └── register.html
└── docs/

## DB Baglantisi
- Host: db (docker-compose icindeki MySQL servisi, container adi: pbimonitor-db)
- Database: pbimonitor
- User: pbimonitor
- Port: 3306
- Tablolar ilk baslatmada init.sql ile otomatik olusur

## Deploy Adimlari (Contabo)
1. Projeyi sunucuya tas: zip ile scp veya git clone
2. .env olustur: cp .env.example .env && nano .env  (DB_PASSWORD, DB_ROOT_PASSWORD, FLASK_SECRET doldur)
3. Baslat: docker compose up -d --build  (tire yok, v2 syntax)
4. Loglar: docker logs pbimonitor-web -f
5. Scheduler loglar: docker logs pbimonitor-scheduler -f
6. DB kontrol: docker exec -it pbimonitor-db mysql -u pbimonitor -pSIFRE pbimonitor

## Kritik Notlar
- Gateway Monitoring icin pbi.py'deki SCOPE'a Gateway.Read.All eklendi. Mevcut kullanicilarin
  eski token/refresh_token'lari bu scope'u icermez - Ayarlar > "Baglantiyi Sifirla" ile yeniden
  device code flow'dan gecmeleri gerekir, aksi halde /api/gateways bos liste doner (401 degil).
- docker-compose degil docker compose (tire yok) - sunucuda v1 yuklu degil
- ALTER TABLE ... ADD COLUMN IF NOT EXISTS MySQL 8.0'da DESTEKLENMIYOR, virgille ayir:
  ALTER TABLE t ADD COLUMN a VARCHAR(255), ADD COLUMN b INT;
- PYTHONUNBUFFERED=1 Dockerfile'da olmali, yoksa scheduler logu gorünmüyor
