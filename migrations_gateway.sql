-- Gateway Monitoring ozelligi icin canli DB'ye uygulanacak migrasyon
-- Contabo'da calistir: docker exec -i pbimonitor-db mysql -u pbimonitor -pSIFRE pbimonitor < migrations_gateway.sql

ALTER TABLE users
    ADD COLUMN gateway_alarm_mail TINYINT DEFAULT 0,
    ADD COLUMN gateway_alarm_whatsapp TINYINT DEFAULT 0,
    ADD COLUMN gateway_alici_mail VARCHAR(255),
    ADD COLUMN gateway_alici_whatsapp VARCHAR(50),
    ADD COLUMN gateway_phone_number_id VARCHAR(255),
    ADD COLUMN gateway_wa_token TEXT;

CREATE TABLE IF NOT EXISTS gateway_status_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    gateway_id VARCHAR(255),
    gateway_name VARCHAR(255),
    datasource_id VARCHAR(255),
    datasource_name VARCHAR(255),
    durum VARCHAR(50),
    mesaj TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
