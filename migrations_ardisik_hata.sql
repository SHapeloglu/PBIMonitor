-- Ardisik Basarisizlik alarmi icin sayac kolonu
-- (ust_uste_hata_esik kolonu zaten mevcut, sadece sayac ekleniyor)
ALTER TABLE dataset_config
    ADD COLUMN ardisik_hata_sayisi INT DEFAULT 0;
