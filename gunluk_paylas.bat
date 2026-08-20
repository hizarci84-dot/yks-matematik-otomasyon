@echo off
chcp 65001 > nul
echo ============================================================
echo      MÜFİT HOCA - GÜNLÜK HİKAYE YAYINLAMA GÖREVİ
echo ============================================================
cd /d "c:\Users\hizar\OneDrive\Desktop\projeler\Riyaziyane içerik üretimi"
python publisher/instagram_publisher.py
echo.
echo Islem tamamlandi.
