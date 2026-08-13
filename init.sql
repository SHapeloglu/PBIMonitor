CREATE DATABASE IF NOT EXISTS pbimonitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE pbimonitor;

CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    plan ENUM('free','pro','enterprise') DEFAULT 'free',
    smtp_host VARCHAR(255),
    smtp_port INT DEFAULT 587,
    smtp_user VARCHAR(255),
    smtp_password VARCHAR(255),
    gateway_alarm_mail TINYINT DEFAULT 0,
    gateway_alarm_whatsapp TINYINT DEFAULT 0,
    gateway_alici_mail VARCHAR(255),
    gateway_alici_whatsapp VARCHAR(50),
    gateway_phone_number_id VARCHAR(255),
    gateway_wa_token TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pbi_connections (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL UNIQUE,
    tenant_id VARCHAR(255),
    token MEDIUMTEXT,
    token_expires_at BIGINT,
    refresh_token MEDIUMTEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS datasets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    pbi_dataset_id VARCHAR(255),
    workspace_id VARCHAR(255),
    workspace_name VARCHAR(255),
    name VARCHAR(255),
    is_active TINYINT DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS dataset_config (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id INT NOT NULL UNIQUE,
    hata_whatsapp TINYINT DEFAULT 0,
    hata_mail TINYINT DEFAULT 0,
    basarili_mail TINYINT DEFAULT 0,
    alici_whatsapp VARCHAR(50),
    alici_mail VARCHAR(255),
    normal_sure INT DEFAULT 300,
    phone_number_id VARCHAR(255),
    wa_token TEXT,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);

CREATE TABLE IF NOT EXISTS alarm_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_id INT NOT NULL,
    durum VARCHAR(50),
    mesaj TEXT,
    kanal VARCHAR(50),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);

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
