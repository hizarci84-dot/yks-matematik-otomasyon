@echo off
cd /d "%~dp0"
echo ============================================================
echo     MUFIT HOCA - NOTEBOOKLM GUNLUK SHORT VIDEO URETICI
echo ============================================================
"C:\Users\hizar\AppData\Local\Python\pythoncore-3.14-64\python.exe" engine/notebooklm_daily_generator.py --push
echo.
echo ============================================================
echo Islem tamamlandi. (Cikis kodu: %ERRORLEVEL%)
if "%~1"=="--nopause" exit /b %ERRORLEVEL%
echo Pencereyi kapatmak icin herhangi bir tusa basin...
pause > nul
