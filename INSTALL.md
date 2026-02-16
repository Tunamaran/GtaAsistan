# GTA Asistan - Kurulum Kılavuzu

## Kullanıcı İçin (Installer ile)

### Adım 1: Setup'ı İndir ve Çalıştır
```
GtaAsistan_Setup_v1.0.0.exe
```

### Adım 2: Kurulum
1. Setup **yönetici yetkisi** isteyecek (gerekli)
2. Kurulum konumunu seç (varsayılan: `C:\Program Files\GTA Asistan`)
3. İsteğe bağlı:
   - ✅ Masaüstü kısayolu
   - ✅ Windows OCR dil paketi kur (Internet gerekli)
4. "Kur" butonuna tıkla

### Adım 3: İlk Çalıştırma
- Masaüstündeki "GTA Asistan" ikonuna çift tıkla
- Launcher açılacak
- "Asistanı Başlat" butonuna tıkla

### Sistem Gereksinimleri
- **Windows 10/11** (64-bit)
- **Python 3.8+** (otomatik kontrol edilir)
- **Internet bağlantısı** (Windows OCR kurulumu için)

### Kaldırma
```
Ayarlar → Uygulamalar → GTA Asistan → Kaldır
```

---

## Geliştirici İçin (Kaynak Koddan Build)

### Ön Gereksinimler
1. **Python 3.8+**
2. **PyInstaller**:
   ```
   pip install pyinstaller
   ```
3. **Inno Setup 6** (Installer oluşturmak için):
   https://jrsoftware.org/isinfo.php

### Bağımlılıkları Yükle
```powershell
pip install -r requirements.txt
```

### Tesseract Portable Hazırla
**Seçenek 1: Manuel İndirme (Önerilen)**
1. İndir: https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.5.0.20241111.exe
2. Kurulum konumu seç: `C:\Users\[KULLANICI]\Desktop\GtaAsistan\tesseract_portable`
3. Kurulum bittiğinde `tesseract_portable\tesseract.exe` olmalı

**Seçenek 2: PowerShell ile Otomatik**
```powershell
Invoke-WebRequest -Uri 'https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.5.0.20241111.exe' -OutFile 'tesseract_setup.exe'
.\tesseract_setup.exe /S /D=$PWD\tesseract_portable
```

### Build
```powershell
.\build.bat
```

**Build adımları:**
1. Icon oluştur (`app_icon.ico`)
2. Tesseract kontrol et
3. `launcher.exe` oluştur (PyInstaller)
4. `main.exe` oluştur (PyInstaller)
5. Dosyaları birleştir (`dist\GtaAsistan\`)
6. Tesseract'ı kopyala
7. Installer oluştur (`Output\GtaAsistan_Setup_v1.0.0.exe`)

### Build Çıktısı
```
dist\GtaAsistan\
├── launcher.exe         (~7 MB)
├── main.exe             (~7 MB)
├── tesseract\           (~60 MB)
├── _internal\           (~220 MB - Python runtime + kütüphaneler)
├── gta_tum_araclar.json (~2 MB)
├── garajim.json
└── app_icon.ico

Output\
└── GtaAsistan_Setup_v1.0.0.exe (~150 MB)
```

### Installer Özellikleri
- **Tesseract OCR** gömülü (portable)
- **Windows OCR dil paketi** otomatik kurulum
- **winocr Python paketi** otomatik kurulum (`pip install winocr`)
- **config.json** otomatik oluşturulur (Tesseract path dahil)
- **Uninstaller** otomatik eklenir

### Sorun Giderme

**Problem: "Tesseract portable bulunamadı"**
```
Çözüm: tesseract_portable\tesseract.exe dosyasının olduğunu doğrula
```

**Problem: "Python bulunamadı" (Installer sırasında)**
```
Çözüm: Python 3.8+ yükle ve PATH'e ekle
```

**Problem: "Inno Setup bulunamadı"**
```
Çözüm: Inno Setup 6 kur veya manuel olarak:
"C:\Users\[KULLANICI]\AppData\Local\Programs\Inno Setup 6\iscc.exe" installer.iss
```

---

## Teknik Detaylar

### PyInstaller Frozen Mod
- `sys.frozen = True`
- `APP_DIR = os.path.dirname(sys.executable)`
- Tüm dosya yolları mutlak (`os.path.join(APP_DIR, ...)`)

### Tesseract Entegrasyonu
- **Konum**: `{app}\tesseract\tesseract.exe`
- **Config**: `config.json` → `"tesseract_path": "C:\Program Files\GTA Asistan\tesseract\tesseract.exe"`

### Windows OCR Kurulumu
```powershell
Add-WindowsCapability -Online -Name "Language.OCR~~~en-US~0.0.1.0"
```

### Otomatik Paket Kurulumu
```bash
pip install winocr
```

---

## Lisans
Bu proje için özel bir lisans bulunmamaktadır.
