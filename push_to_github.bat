@echo off
echo ===================================================
echo   YKS MATEMATIK OTOMASYONU - GITHUB YUKLEME
echo ===================================================
echo.

git remote remove origin 2>nul
git remote add origin https://github.com/hizarci84-dot/yks-matematik-otomasyon.git
git branch -M main

echo Dosyalar yukleniyor, lutfen bekleyin...
git push -u origin main

echo.
echo ===================================================
echo   Islem tamamlandi!
echo ===================================================
pause
