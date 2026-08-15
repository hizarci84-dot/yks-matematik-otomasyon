@echo off
chcp 65001 > nul
echo =======================================================
echo    MÜFİT HOCA İLE MATEMATİK - GITHUB YÜKLEME ARACI
echo =======================================================
echo.
set /p REPO_URL="Lütfen GitHub Repo URL'inizi yapıştırın (Örn: https://github.com/kullanici/repo.git): "

if "%REPO_URL%"=="" (
    echo [HATA] URL girmediniz. Lutfen tekrar deneyin.
    pause
    exit /b
)

echo.
echo [1/3] Git remote baglantisi ayarlaniyor...
git remote remove origin 2>nul
git remote add origin %REPO_URL%

echo [2/3] Branch main olarak ayarlaniyor...
git branch -M main

echo [3/3] Dosyalar GitHub'a yukleniyor (git push)...
git push -u origin main

echo.
echo =======================================================
echo    TEBRİKLER! Dosyalar GitHub'a başarıyla yüklendi.
echo =======================================================
pause
