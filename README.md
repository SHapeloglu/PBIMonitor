# PBIMonitor

**Power BI Monitoring SaaS** — Multi-tenant, açık kaynak bir izleme platformu.

Power BI'ın yerli araçlarının açığa çıkarmadığı dataset yenileme başarısızlıklarını, gateway sorunlarını ve anormallikleri algılayıp uyarı gönderir.

🌐 **Canlı:** https://95.111.242.96:8003

---

## Özellikler

### 8 Uyarı Koşulu
1. **Ardışık Başarısızlık** — Başarısız yenileme denemelerini sayaçla
2. **Sıfır Süre Yenileme** — Eksik/hayalet yenilemeler (0 saniye = veri yok)
3. **Kaçırılan Yenileme** — Beklenen zamanda yenileme olmadığında uyar
4. **Anomali Tespiti** — Sürede anormal artışları algıla
5. **Devre Kapalı** — Dataset zamanlaması kapatıldığında yakala
6. **Gateway Çöktü** — Power BI gateway durumunu izle
7. **Dataset Sayısı Uyumsuzluğu** — Dataset değişikliklerini takip et
8. **Uyarılarla Tamamlandı** *(Denendi — Power BI API kısıtlaması)*

### Altyapı
- **Multi-Tenant** — Azure AD OAuth
- **Şifreleme** — Fernet AES-128
- **Uyarılar** — WhatsApp + Email
- **Mobil Uyumlu** — Responsive hamburger menü
- **Yenileme Geçmişi** — Chart.js grafikleri
- **Docker Compose** — 3 konteyner

---

## Teknoloji Yığını

- **Backend:** Flask + PyMySQL
- **Veritabanı:** MySQL 8.0
- **Frontend:** Vanilla JS, Chart.js, CSS Responsive
- **Kimlik Doğrulama:** Azure AD OAuth
- **Planlayıcı:** Python daemon (30 dakika)
- **Uyarılar:** Meta Graph API, SMTP

---

## Hızlı Başlangıç

```bash
git clone https://github.com/SHapeloglu/PBIMonitor.git
cd PBIMonitor
cp .env.example .env
docker compose up -d
```

**Erişim:** http://localhost:8003

---

## API Uç Noktaları

| Method | Uç Nokta | Açıklama |
|--------|----------|----------|
| GET | `/` | Kontrol Paneli |
| GET | `/api/datasets` | Veri setlerini listele |
| POST | `/api/kontrol` | Anlık yenileme kontrolü |
| GET | `/api/alarm_log` | Uyarı geçmişi |
| GET | `/api/refresh_history/<id>` | Yenileme grafiği |

---

## Veritabanı

**9 Tablo:** users, pbi_connections, datasets, dataset_config, refresh_history, alarm_log, alarm_history, gateway_health, gateway_log

**Şifreli Alanlar:** tokens, credentials (Fernet AES-128)

---

## Duyarlı Tasarım

| Ekran | Sidebar | Grid |
|-------|---------|------|
| Masaüstü (≥769px) | Sabit | 4 sütun |
| Tablet (≤768px) | Hamburger | 2 sütun |
| Mobil (≤420px) | Hamburger | 1 sütun |

---

## Bilinen Sınırlamalar

### Power BI API Kısıtlamaları
- "Uyarılarla Tamamlandı" — API'de veri yok
- Kimlik bilgisi süresi — Sınırlı destek
- Kapasite aşımı — Premium-only
- Sıfır satır tespiti — API yok

### Desteklenen Kanallar
- ✅ WhatsApp, Email
- ⏸ Teams, Slack, Telegram

---

## Geliştirme

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

---

## Dokümantasyon

- [SESSION.md](docs/SESSION.md) — Mevcut durum
- [ARCHITECT.md](docs/ARCHITECT.md) — Sistem tasarımı
- [ERRORS.md](docs/ERRORS.md) — Bilinen sorunlar
- [BACKLOG.md](docs/BACKLOG.md) — Yol haritası

---

## Lisans

MIT

---

**Durum:** ✅ v1.2 — Responsive UI Complete  
**Son Güncelleme:** 16 Ağustos 2026  
**Repo:** https://github.com/SHapeloglu/PBIMonitor
