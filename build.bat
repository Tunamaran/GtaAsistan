@echo off
REM ============================================
REM  GTA Asistan - Build Script
REM  Bu dosya PyInstaller ile exe oluşturur
REM ============================================

echo.
echo ========================================
echo   GTA Asistan - Build Baslatiliyor
echo ========================================
echo.

REM Eski build dosyalarini temizle
echo [1/5] Eski build dosyalari temizleniyor...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM Icon olustur (yoksa)
echo [2/5] Uygulama ikonu kontrol ediliyor...
if not exist "app_icon.ico" (
    echo   Icon bulunamadi, olusturuluyor...
    python create_icon.py
)

REM Launcher.exe olustur
echo [3/5] Launcher.exe olusturuluyor...
pyinstaller launcher.spec --noconfirm
if errorlevel 1 (
    echo HATA: Launcher build basarisiz!
    pause
    exit /b 1
)

REM Main.exe olustur
echo [4/5] Main.exe olusturuluyor...
pyinstaller main.spec --noconfirm
if errorlevel 1 (
    echo HATA: Main build basarisiz!
    pause
    exit /b 1
)

REM Main.exe dosyalarini Launcher klasorune kopyala
echo [5/5] Dosyalar birlestiriliyor...
xcopy /s /y /q "dist\GtaAsistan_Main\main.exe" "dist\GtaAsistan\"

REM GtaAsistan_Main klasorunu temizle
rmdir /s /q "dist\GtaAsistan_Main"

REM Veri dosyalarini kopyala
copy /y "gta_tum_araclar.json" "dist\GtaAsistan\"
copy /y "app_icon.ico" "dist\GtaAsistan\"

REM Bos garaj dosyasi olustur
echo [] > "dist\GtaAsistan\garajim.json"

echo.
echo ========================================
echo   Build Tamamlandi!
echo   Cikti: dist\GtaAsistan\
echo ========================================
echo.
echo   launcher.exe - Ana program
echo   main.exe     - Asistan motoru
echo.

REM Inno Setup ile installer olustur (varsa)
where iscc >nul 2>&1
if %errorlevel%==0 (
    echo [BONUS] Installer olusturuluyor...
    iscc installer.iss
    echo   Installer: Output\GtaAsistan_Setup.exe
) else (
    echo [BILGI] Inno Setup bulunamadi.
    echo   Installer icin Inno Setup yukleyin:
    echo   https://jrsoftware.org/isinfo.php
    echo   Sonra "iscc installer.iss" calistirin.
)

echo.
pause
