@echo off
REM ============================================
REM  GTA Asistan - Build Script
REM  Bu dosya PyInstaller ile exe oluşturur
REM ============================================

REM Sanal Ortamı Aktive Et
if exist ".\.venv\Scripts\activate.bat" (
    echo [BILGI] Sanal ortam aktif ediliyor...
    call ".\.venv\Scripts\activate.bat"
)

echo.
echo ========================================
echo   GTA Asistan - Build Baslatiliyor
echo ========================================

REM Version update
echo [0/7] Surum guncelleniyor...
python update_version.py
if errorlevel 1 (
    echo HATA: Version guncelleme basarisiz!
    pause
    exit /b 1
)

echo.

REM Eski build dosyalarini temizle
echo [1/7] Eski build dosyalari temizleniyor...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

REM Icon kontrol
echo [2/7] Uygulama ikonu kontrol ediliyor...
if not exist "app_icon.ico" (
    echo   UYARI: app_icon.ico bulunamadi! Lutfen proje dizinine ekleyin.
    pause
    exit /b 1
)

REM Tesseract portable kontrol
echo [3/7] Tesseract OCR kontrol ediliyor...
if not exist "tesseract_portable\tesseract.exe" (
    echo.
    echo   ================================================================
    echo   UYARI: Tesseract portable bulunamadi!
    echo   ================================================================
    echo.
    echo   Tesseract installer'a gomulmesi icin asagidaki adimlari izleyin:
    echo.
    echo   1. Indir: https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.5.0.20241111.exe
    echo   2. Setup'i calistir, kurulum yeri secerken "tesseract_portable" klasorunu secin
    echo   3. Kurulum bittikten sonra bu scripti tekrar calistirin
    echo.
    echo   VEYA
    echo.
    echo   Otomatik indirme icin asagidaki komutu calistirin:
    echo   powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.5.0.20241111.exe' -OutFile 'tesseract_setup.exe'"
    echo   tesseract_setup.exe /S /D=%%CD%%\tesseract_portable
    echo.
    echo   ================================================================
    echo.
    pause
    exit /b 1
) else (
    echo   Tesseract bulundu: tesseract_portable\tesseract.exe
)

REM Launcher.exe olustur
echo [4/7] Launcher.exe olusturuluyor...
pyinstaller launcher.spec --noconfirm
if errorlevel 1 (
    echo HATA: Launcher build basarisiz!
    pause
    exit /b 1
)

REM Main.exe olustur
echo [5/7] Main.exe olusturuluyor...
pyinstaller main.spec --noconfirm
if errorlevel 1 (
    echo HATA: Main build basarisiz!
    pause
    exit /b 1
)

REM Main.exe dosyalarini Launcher klasorune kopyala
echo [6/7] Dosyalar birlestiriliyor...
xcopy /s /y /q "dist\GtaAsistan_Main\main.exe" "dist\GtaAsistan\"

REM GtaAsistan_Main klasorunu temizle
rmdir /s /q "dist\GtaAsistan_Main"

REM Veri dosyalarini kopyala
copy /y "gta_tum_araclar.json" "dist\GtaAsistan\"
copy /y "app_icon.ico" "dist\GtaAsistan\"

REM Bos garaj dosyasi olustur
echo [] > "dist\GtaAsistan\garajim.json"

REM Tesseract'i dist'e kopyala
echo [7/7] Tesseract kopyalaniyor...
xcopy /s /y /q /i "tesseract_portable" "dist\GtaAsistan\tesseract"

echo.
echo ========================================
echo   Build Tamamlandi!
echo   Cikti: dist\GtaAsistan\
echo ========================================
echo.
echo   launcher.exe - Ana program
echo   main.exe     - Asistan motoru
echo   tesseract\   - OCR motoru
echo.

REM Inno Setup ile installer olustur (varsa)
set ISCC_PATH=C:\Users\%USERNAME%\AppData\Local\Programs\Inno Setup 6\iscc.exe
if exist "%ISCC_PATH%" (
    echo [BONUS] Installer olusturuluyor...
    "%ISCC_PATH%" installer.iss
    if errorlevel 1 (
        echo HATA: Installer olusturma basarisiz!
        pause
        exit /b 1
    )
    for /f "tokens=2 delims==" %%v in ('findstr /b /c:"OutputBaseFilename=" installer.iss') do set OUTPUT_BASE=%%v
    if defined OUTPUT_BASE (
        echo   Installer: Output\%OUTPUT_BASE%.exe
    ) else (
        echo   Installer olustu. Dosya adi installer.iss icindeki OutputBaseFilename degerine gore belirlenir.
    )
) else (
    echo [BILGI] Inno Setup bulunamadi.
    echo   Installer icin Inno Setup yukleyin:
    echo   https://jrsoftware.org/isinfo.php
)

echo.
echo ========================================
echo   KURULUM NOTLARI
echo ========================================
echo.
echo   Installer su paketleri otomatik kuracak:
echo   - Windows OCR dil paketi (Internet gerekli)
echo   - winocr Python paketi (pip install)
echo.
echo   Tesseract zaten installer'a gomulu.
echo.
pause
