@echo off
cd /d "%~dp0"
echo ============================================================
echo        NOTEBOOKLM GOOGLE HESABINA GIRIS (TEK SEFERLIK)
echo ============================================================
echo Acilacak tarayici penceresinde Google hesabinizla giris yapin.
echo Giris tamamlandiginda oturum otomatik olarak kaydedilecektir.
echo.
"C:\Users\hizar\AppData\Local\Python\pythoncore-3.14-64\Scripts\notebooklm.exe" login
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
