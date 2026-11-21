@echo off
cd /d "%~dp0"
echo ============================================================
echo     NOTEBOOKLM KALICI OTURUM GIRISI (MASTER TOKEN MODU)
echo ============================================================
echo Acilacak tarayici penceresinde Google hesabinizla (hizarci84@gmail.com)
echo giris yapin. Kalici master_token olusturulacagi icin PC gunlerce
echo kapali kalsa bile oturum otomatik yenilenecektir.
echo.
"C:\Users\hizar\AppData\Local\Python\pythoncore-3.14-64\Scripts\notebooklm.exe" login --master-token --account hizarci84@gmail.com --force
if errorlevel 1 (
    echo.
    echo Master token girisi tamamlanamadi, standart giris deneniyor...
    "C:\Users\hizar\AppData\Local\Python\pythoncore-3.14-64\Scripts\notebooklm.exe" login
)
echo.
echo Oturum dogrulaniyor...
"C:\Users\hizar\AppData\Local\Python\pythoncore-3.14-64\Scripts\notebooklm.exe" auth check --test
echo.
echo NotebookLM baglanti ve konu secim testi yapiliyor...
"C:\Users\hizar\AppData\Local\Python\pythoncore-3.14-64\python.exe" engine/notebooklm_daily_generator.py --dry-run
echo.
echo ============================================================
echo Pencereyi kapatmak icin herhangi bir tusa basin...
pause > nul
