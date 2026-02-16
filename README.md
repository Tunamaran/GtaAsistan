# 🎮 GTA Asistan (Jarvis)

**GTA V için yapay zeka destekli araç tanıma asistanı**

Ekrandaki araç isimlerini gerçek zamanlı olarak okur ve detaylı bilgileri overlay (katman) ile gösterir.

---

## ✨ Özellikler

- ⚡ **Hızlı OCR**: Windows OCR (30ms) veya Tesseract
- 🎯 **Akıllı Tanıma**: TheFuzz ile fuzzy matching
- 📊 **Detaylı Bilgiler**: Fiyat, hız, sınıf, özellikler
- 🏠 **Garaj Yönetimi**: Sahip olduğunuz araçları kaydedin
- 🖼️ **Galeri**: 500+ araç veritabanı, filtreleme, arama
- 🏷️ **Akıllı Rozetler**: "F/P Canavarı", "Lüks", "Roket" vs.
- ⌨️ **Kısayollar**: F9 (Garaj), F10 (OCR Duraklat), F11 (Galeri)
- 🎨 **Modern Karanlık Tema**: Yeşil vurgulu minimalist tasarım

---

## 🚀 Hızlı Kurulum

### Adım 1: Installer'ı İndir
```
GtaAsistan_Setup_v1.0.0.exe
```

### Adım 2: Kur ve Çalıştır
1. Setup'ı çalıştır (Admin yetkisi isteyecek)
2. "İleri" → "Kur"
3. Masaüstündeki ikona çift tıkla
4. "Asistanı Başlat"

**O kadar!** Hiçbir manuel kurulum gerekmiyor.

---

## 📦 Otomatik Kurulum

Installer aşağıdakileri otomatik kurar:

- ✅ **Tesseract OCR** (gömülü, ~60MB)
- ✅ **Windows OCR dil paketi** (opsiyonel, Internet gerekli)
- ✅ **winocr Python paketi** (opsiyonel)
- ✅ **config.json** (otomatik ayarlar)

> **Not:** Python yüklemenize gerek yok! Tüm bağımlılıklar exe'ye gömülüdür.

---

## 🎯 Kullanım

### Launcher
- **Asistanı Başlat**: Ana programı başlatır
- **Ayarlar**: OCR bölgesi, Tesseract yolu, kısayollar
- **Veri Güncelleme**: GTABase.com'dan araç verilerini çek
- **Fabrika Ayarları**: Tüm ayarları sıfırla

### Asistan (Ana Program)
1. **GTA V'yi başlat**
2. Araç satın alma menüsünü aç
3. Araç isimlerinin üzerine gel
4. **Otomatik bilgi kartı** görünür

### Kısayollar
- **F9**: Garaj yönetimi (sahip olduğunuz araçlar)
- **F10**: OCR duraklat/devam ettir
- **F11**: Galeri (tüm araçlar)

---

## 🛠️ Geliştirici İçin

### Kaynak Koddan Build

**1. Bağımlılıkları Yükle**
```powershell
pip install -r requirements.txt
```

**2. Tesseract Portable Hazırla**
```
İndir: https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.5.0.20241111.exe
Kur: tesseract_portable\ klasörüne
```

**3. Build**
```powershell
.\build.bat
```

**Çıktı:**
- `dist\GtaAsistan\` (portable uygulama)
- `Output\GtaAsistan_Setup_v1.0.0.exe` (installer)

Detaylı dokümantasyon: [INSTALL.md](INSTALL.md)

---

## 📋 Sistem Gereksinimleri

- **Windows 10/11** (64-bit)
- **Internet** (opsiyonel - Windows OCR için)
- **~300MB disk alanı**

---

## 🤝 Katkıda Bulunma

Pull request'ler kabul edilir! Büyük değişiklikler için önce issue açın.

---

## 📄 Lisans

Bu proje özel bir lisans altında değildir.

---

## 🎮 Ekran Görüntüleri

### Launcher
Modern karanlık tema, kolay ayar yönetimi

### HUD (Bilgi Ekranı)
Araç resmi, fiyat, hız, özel etiketler

### Galeri
500+ araç, filtreleme, sayfalama

### Garaj Analizi
Sınıf dağılımı, rekorlar, eksik sınıflar

---

## ⚙️ Teknoloji

- **Python 3.12** + PyQt5
- **OCR**: Windows OCR (winocr) / Tesseract
- **Görüntü İşleme**: OpenCV, NumPy
- **Veri**: GTABase.com scraper (Cloudscraper)
- **Build**: PyInstaller + Inno Setup

---

## 📞 Destek

Sorun bildirmek için [Issues](https://github.com/tunamaran/GtaAsistan/issues) bölümünü kullanın.

---

**🎉 İyi oyunlar!**
