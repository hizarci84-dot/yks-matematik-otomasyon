@echo off
chcp 65001 > nul
echo ============================================================
echo     MUFIT HOCA - NOTEBOOKLM GUNLUK SHORT VIDEO URETICI
echo ============================================================
cd /d "c:\Users\hizar\OneDrive\Desktop\projeler\Riyaziyane içerik üretimi"
"C:\Users\hizar\AppData\Local\Python\pythoncore-3.14-64\python.exe" engine/notebooklm_daily_generator.py --push
echo.
echo ============================================================
echo Islem tamamlandi. (Cikis kodu: %ERRORLEVEL%)
if "%~1"=="--nopause" exit /b %ERRORLEVEL%
echo Pencereyi kapatmak icin herhangi bir tusa basin...
pause > nul
