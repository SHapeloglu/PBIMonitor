# Bilinen Hatalar ve Cozumleri

## cursor(dictionary=True) hatasi
Hata: TypeError: Connection.cursor() got an unexpected keyword argument 'dictionary'
Neden: PyMySQL bu parametreyi desteklemiyor
Cozum: cursor() kullan, DictCursor db.py'de zaten tanimli

## DB Access Denied
Hata: Access denied for user
Neden: mysql.connector MariaDB ile uyumsuz veya sifre yanlis
Cozum: PyMySQL kullan, .env dosyasindaki sifreyi kontrol et

## Emoji DB hatasi
Hata: Incorrect string value '\xE2\x9C\x85...'
Cozum: monitor.py'de emoji kullanma, mesajlari ASCII ile yaz

## Token gecersiz
Hata: 401 Power BI API
Neden: Token suresi dolmus (1 saat)
Cozum: pbi.py'de token_yenile() ile otomatik yenileniyor (refresh_token DB'de kayitli)
Not: refresh_token NULL olan eski kullanicilar bir kerelik yeniden baglanmali

## Docker baglanti sorunu
Hata: DB'ye baglanamadi
Cozum: Artik ayri pbimonitor-db container var, DB_HOST=db (.env'de)

## ALTER TABLE IF NOT EXISTS hatasi
Hata: ERROR 1064 - syntax error near 'IF NOT EXISTS smtp_host'
Neden: MySQL 8.0 ADD COLUMN IF NOT EXISTS desteklemiyor
Cozum: Virgille ayir: ALTER TABLE t ADD COLUMN a VARCHAR(255), ADD COLUMN b INT;

## Scheduler logu gorünmüyor
Hata: docker logs pbimonitor-scheduler bos donüyor
Neden: Python print() buffered modda calisıyor
Cozum: Dockerfile'a ENV PYTHONUNBUFFERED=1 ekle

## docker-compose command not found
Hata: Command 'docker-compose' not found
Neden: Sunucuda Docker Compose v1 yuklu degil
Cozum: docker compose (tire yok, v2 syntax) kullan

## Gateway listesi bos donuyor
Hata: /gateway sayfasinda "erisebildiginiz bir gateway bulunamadi" mesaji, gateway var olmasina ragmen
Neden: Gateway.Read.All scope'u sonradan eklendi, eski token/refresh_token bu izni icermiyor
Cozum: Ayarlar sayfasindan "Baglantiyi Sifirla" ile PBI baglantisini yeniden kur (device code flow tekrar calisir, yeni scope'lar onaylanir)

## Ayarlar modal acilmiyor
Hata: Cog butonuna tiklaninca modal acilmiyor
Neden: onclick attribute icine JSON.stringify gomuluyordu, JSON'daki cift tirnak HTML attribute'unu bozuyordu
Cozum: datasetMap JS objesi ile id->dataset esleme, onclick'e sadece id gec
