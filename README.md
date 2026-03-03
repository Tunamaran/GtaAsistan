# 🎮 GTA Asistan / GTA Assistant

<div align="center">

[🇹🇷 Türkçe](#-gta-asistan-jarvis) &nbsp;&nbsp;|&nbsp;&nbsp; [🇺🇸 English](#-gta-assistant-jarvis)

</div>

<br>

---

# 🇹🇷 GTA Asistan (Jarvis)

**GTA V için yapay zeka destekli araç tanıma asistanı**

Ekrandaki araç isimlerini gerçek zamanlı olarak okur ve detaylı bilgileri overlay (katman) ile gösterir.

## ✨ Özellikler

- ⚡ **Akıllı OCR**: OpenCV renk maskeleme + Windows OCR (otomatik menü algılama)
- 🎯 **Akıllı Tanıma**: TheFuzz ile bulanık eşleşme (fuzzy matching)
- 🎮 **GTA V Enhanced Desteği**: Hem klasik hem Enhanced/BattlEye sürümleri
- 📊 **Detaylı Bilgiler**: Fiyat, hız, sınıf, özellikler
- 🏠 **Garaj Yönetimi**: Sahip olduğunuz araçları kaydedin
- 🖼️ **Galeri**: 500+ araç veritabanı, filtreleme, arama
- 🏷️ **Akıllı Rozetler**: "F/P Canavarı", "Lüks", "Roket" vb.
- ⌨️ **Kısayollar**: F9 (Garaj), F10 (OCR Duraklat), F11 (Galeri)
- 🎨 **Modern Karanlık Tema**: Yeşil vurgulu minimalist tasarım

---

## 🚀 Hızlı Kurulum

### Adım 1: Kurulum için aşağıdaki bağlantıdan yükleyiciyi indirebilirsiniz:
[**Son Sürümü İndir / Download Latest Release**](https://github.com/tunamaran/GtaAsistan/releases/latest)

### Adım 2: Kur ve Çalıştır
1. Setup dosyasını çalıştırın (Yönetici izni gereklidir).
2. "İleri" → "Kur" adımlarını izleyin.
3. Masaüstündeki ikona çift tıklayın.
4. "Asistanı Başlat" butonuna basın.

**Bu kadar!** Hiçbir manuel ayar gerekmez.

---

## 📦 Kurulum İçeriği

Installer aşağıdakileri otomatik kurar:

- ✅ **Tesseract OCR** (gömülü, yedek motor)
- ✅ **Windows OCR dil paketi** (opsiyonel, internet gerekir)
- ✅ **Gerekli Python paketleri** (exe içine gömülü)
- ✅ **config.json** (varsayılan ayarlar)

> **Not:** Bilgisayarınızda Python yüklü olmasına gerek yoktur!

---

## 🎯 Kullanım

### Launcher (Başlatıcı)
- **Asistanı Başlat**: Ana programı başlatır.
- **Ayarlar**: HUD konumu, kısayollar ve diğer ayarlar.
- **Veri Güncelleme**: GTABase.com'dan en güncel araç verilerini çeker.
- **Fabrika Ayarları**: Tüm ayarları varsayılana döndürür.

### Asistan (Oyun İçi)
1. **GTA V'yi başlatın.** (Klasik, Enhanced veya BattlEye sürümü)
2. **Mekanik**, **Pegasus** veya **Etkileşim Menüsü (Interaction Menu)** gibi araç listesi olan menüleri açın.
3. Menüdeki yön tuşları veya butonlar ile araç isminin üzerine gelin.
4. **Otomatik bilgi kartı** ekranda belirecektir.

> **Not:** Araç satın alma sitelerinde çalışmaz. Sadece oyun içi menülerde aktiftir.

### Kısayollar
- **F9**: Garaj yönetimi (Aracı garajınıza ekler/çıkarır).
- **F10**: OCR işlemini geçici olarak duraklatır/devam ettirir.
- **F11**: Araç Galerisini açar/kapatır.

---

## 🛠️ Geliştiriciler İçin

### Kaynak Koddan Derleme (Build)

**1. Bağımlılıkları Yükleyin**
```powershell
pip install -r requirements.txt
```

**2. Tesseract Portable Hazırlayın**
```
İndirin: https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.5.0.20241111.exe
Yükleyin/Kopyalayın: Proje dizininde `tesseract_portable\` klasörüne.
```

**3. Derleyin**
```powershell
.\build.bat
```

**Çıktı:**
- `dist\GtaAsistan\` (Taşınabilir klasör)
- `Output\GtaAsistan_Setup_v1.0.0.exe` (Yükleyici)

Detaylı dokümantasyon için: [INSTALL.md](INSTALL.md)

---

## 📋 Sistem Gereksinimleri

- **Windows 10/11** (64-bit)
- **İnternet Bağlantısı** (İlk kurulum ve Windows OCR indirimi için önerilir)
- **~150MB Disk Alanı**

## 📸 Ekran Görüntüleri

| Görünüm 1 | Görünüm 2 |
|:---:|:---:|
| ![Ekran Görüntüsü 1](docs/images/screenshot1.png) | ![Ekran Görüntüsü 2](docs/images/screenshot2.png) |

| Görünüm 3 | Görünüm 4 |
|:---:|:---:|
| ![Ekran Görüntüsü 3](docs/images/screenshot3.png) | ![Ekran Görüntüsü 4](docs/images/screenshot4.png) |


## 🤝 Katkıda Bulunma

Pull request'ler kabul edilir! Büyük değişiklikler için lütfen önce Issue açarak tartışın.

## 📄 Lisans

Bu proje herhangi bir özel lisans altında değildir.

## 🙏 Teşekkürler

Bu projenin geliştirilmesinde emeği geçen herkese teşekkürler.

- [GTABase](https://www.gtabase.com/) - Araç verileri için
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - OCR motoru için
- [TheFuzz](https://github.com/seatgeek/thefuzz) - Bulanık eşleşme algoritması için
- [OpenCV](https://opencv.org/) - Bilgisayarla görü tabanlı menü algılama için

---

<br><br>

# 🇺🇸 GTA Assistant (Jarvis)

**AI-powered vehicle recognition assistant for GTA V**

Real-time vehicle name recognition via OCR, displaying detailed information via an in-game overlay.

## ✨ Features

- ⚡ **Smart OCR**: OpenCV color masking + Windows OCR (automatic menu detection)
- 🎯 **Smart Recognition**: Fuzzy matching with TheFuzz for accurate detection.
- 🎮 **GTA V Enhanced Support**: Works with Classic, Enhanced, and BattlEye editions.
- 📊 **Detailed Info**: Price, speed, class, specifications.
- 🏠 **Garage Management**: Track vehicles you own.
- 🖼️ **Gallery**: Database of 500+ vehicles with filtering and search.
- 🏷️ **Smart Badges**: "Value King", "Luxury", "Rocket", etc.
- ⌨️ **Shortcuts**: F9 (Garage), F10 (Pause OCR), F11 (Gallery).
- 🎨 **Modern Dark Theme**: Minimalist design with green accents.

---

## 🚀 Quick Setup

### Step 1: You can download the installer from the following link:
[**Download Latest Release**](https://github.com/tunamaran/GtaAsistan/releases/latest)

### Step 2: Install & Run
1. Run the setup file (Requires Admin privileges).
2. Click "Next" → "Install".
3. Double-click the icon on your Desktop.
4. Click "Start Assistant".

**That's it!** No manual configuration required.

---

## 📦 What's Inside

The installer automatically sets up:

- ✅ **Tesseract OCR** (embedded, fallback engine)
- ✅ **Windows OCR language pack** (optional, requires internet)
- ✅ **Required Python packages** (embedded in exe)
- ✅ **config.json** (default settings)

> **Note:** Python is NOT required on your system!

---

## 🎯 Usage

### Launcher
- **Start Assistant**: Launches the main application.
- **Settings**: Configure HUD position, shortcuts, etc.
- **Update Data**: Fetches the latest vehicle data from GTABase.com.
- **Factory Reset**: Resets all settings to default.

### Assistant (In-Game)
1. **Start GTA V.** (Classic, Enhanced, or BattlEye edition)
2. Open menus like **Mechanic**, **Pegasus**, or **Interaction Menu** where vehicle lists appear.
3. Navigate to the vehicle name using menu buttons/keys.
4. The **info card overlay** will appear automatically.

> **Note:** Does not work on vehicle purchase websites. Only active in in-game menus.

### Shortcuts
- **F9**: Garage management (Add/Remove vehicle from your garage).
- **F10**: Pause/Resume OCR engine.
- **F11**: Toggle Vehicle Gallery.

---

## 🛠️ For Developers

### Building from Source

**1. Install Dependencies**
```powershell
pip install -r requirements.txt
```

**2. Prepare Portable Tesseract**
```
Download: https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.5.0.20241111.exe
Install/Copy to: `tesseract_portable\` folder in the project root.
```

**3. Build**
```powershell
.\build.bat
```

**Output:**
- `dist\GtaAsistan\` (Portable folder)
- `Output\GtaAsistan_Setup_v1.0.0.exe` (Installer)

See docs: [INSTALL.md](INSTALL.md)

---

## 📋 System Requirements

- **Windows 10/11** (64-bit)
- **Internet Connection** (Recommended for initial setup and Windows OCR)
- **~150MB Disk Space**

## 📸 Screenshots

| View 1 | View 2 |
|:---:|:---:|
| ![Screenshot 1](docs/images/screenshot1.png) | ![Screenshot 2](docs/images/screenshot2.png) |

| View 3 | View 4 |
|:---:|:---:|
| ![Screenshot 3](docs/images/screenshot3.png) | ![Screenshot 4](docs/images/screenshot4.png) |


## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## 📄 License

This project is not under any specific license.

## 🙏 Acknowledgements

Thanks to everyone who contributed to the development of this project.

- [GTABase](https://www.gtabase.com/) - For vehicle data
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - For OCR engine
- [TheFuzz](https://github.com/seatgeek/thefuzz) - For fuzzy matching algorithm
- [OpenCV](https://opencv.org/) - For computer vision based menu detection

---

## 📞 Support / Destek

For issues, please use the [Issues](https://github.com/tunamaran/GtaAsistan/issues) section.

**🎉 Enjoy the game / İyi oyunlar!**
