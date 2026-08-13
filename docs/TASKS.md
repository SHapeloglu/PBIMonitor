# Bekleyen Gorevler

## Oncelikli
- [x] Ayarlar modal acilmiyor (cog butonu) - onclick icine JSON gomulurken cift tirnak HTML attribute'unu bozuyordu, datasetMap ile cozuldu
- [x] Refresh token - token dolunca otomatik yenile (pbi.py: token_yenile fonksiyonu, DB migrasyonu docs/DB_SCHEMA.md'de)
- [x] Cron job - her 30 dakikada otomatik kontrol (scheduler.py, docker-compose'da ayri servis)
- [x] Contabo Docker deploy - tamamlandi (kendi MySQL container'i, init.sql ile otomatik tablo kurulumu)

## Orta Vade
- [x] Alarm log sayfasi - gecmis alarmlar gorunsun (/alarm-log route + alarm_log.html)
- [x] SMTP ayarlari - arayuzden girilebilsin (/ayarlar route + ayarlar.html, users tablosuna smtp kolonlari)
- [ ] .pbix parse - model analizi
- [ ] DAX anti-pattern tespiti
- [ ] SQL Server DMV baglantisi
- [x] Gateway Monitoring - /gateway sayfasi + api/gateways, api/gateway_kontrol, api/gateway_log; scheduler'a entegre edildi
      NOT: Gateway.Read.All scope'u yeni eklendi, mevcut kullanicilarin Ayarlar > "Baglantiyi Sifirla" ile
      PBI baglantisini yeniden yapmasi gerekiyor, aksi halde gateway listesi bos doner.

## Uzun Vade
- [ ] MySQL sonrasi PostgreSQL, Oracle destegi
- [ ] Teams, Telegram, Slack, PagerDuty entegrasyonu
- [ ] Scanner API
- [ ] Performans Tanilama modulu
- [ ] Token yenileme: bireysel=refresh token, kurumsal=service principal
