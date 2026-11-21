@echo off
cd /d "%~dp0"
echo ============================================================
echo   WINDOWS GUNLUK OTOMATIK VIDEO URETIM GOREVI KURULUMU
echo ============================================================
echo Her gun saat 08:00'de veya PC ilk acildiginda NotebookLM'den
echo 1 yeni Short video uretip kuyruga ekleyen gorev kuruluyor...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command "$t1 = New-ScheduledTaskTrigger -Daily -At '08:00'; $t2 = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME; $t2.Delay = 'PT1M'; Register-ScheduledTask -TaskName 'MufitHoca_NotebookLM_Gunluk_Video' -Action (New-ScheduledTaskAction -Execute 'C:\Users\hizar\AppData\Local\Python\pythoncore-3.14-64\pythonw.exe' -Argument 'engine/notebooklm_daily_generator.py --push' -WorkingDirectory (Get-Location).Path) -Trigger @($t1, $t2) -Settings (New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries) -Description 'Her gun NotebookLM uzerinden 1 yeni Short video uretip 60 sn altina uyarlayarak Instagram kuyruguna ekler.' -Force"
echo.
echo ============================================================
echo Pencereyi kapatmak icin herhangi bir tusa basin...
pause > nul
