# Proje Durumu

## Proje Hakkında
**Adı:** GTA Asistan (Jarvis)
**Özet:** GTA V oyununda ekrandaki araç isimlerini OCR (Optik Karakter Tanıma) ile okuyarak, araç hakkında detaylı bilgileri (fiyat, hız, sınıf vb.) oyuncuya overlay (katman) şeklinde sunan bir yardımcı araç. Ayrıca manuel olarak araçları inceleyebileceğiniz bir "Galeri" ve sahip olduğunuz araçları kaydedebileceğiniz bir "Garaj" sistemi içerir.

## Teknoloji Yığını
- **Dil:** Python 3.x
- **Arayüz:** PyQt5 (Modern, karanlık tema, overlay pencereler)
- **OCR & Görüntü İşleme:** Tesseract-OCR, OpenCV (cv2), MSS (ekran görüntüsü), NumPy
- **Veri Eşleştirme:** TheFuzz (fuzzy string matching)
- **Veri Kaynağı:** GTABase.com (Scraper: `VeriÇek.py`)
- **Veri Tabanı:** JSON (`gta_tum_araclar.json`, `garajim.json`)
- **Diğer:** Requests (resim indirme), Keyboard (kısayollar)

## Dosya Yapısı
- **main.py:** Uygulamanın giriş noktası. `JarvisApp` sınıfı burada başlatılır.
- **ui.py:** Kullanıcı arayüzü (OverlayHUD, Galeri, Kart tasarımı) kodları.
- **workers.py:** Arka plan işlemleri (OCR taraması, Klavye dinleme, Resim indirme).
- **database.py:** Veritabanı işlemleri (JSON okuma/yazma, istatistikler, rozet mantığı).
- **config.py:** Ayar dosyası okuma/yazma işlemleri.
- **config.json:** Kullanıcı ayarları (Tesseract yolu, kısayollar, OCR bölgesi).
- **VeriÇek.py:** GTABase sitesinden araç verilerini çeken bot (Scraper).
- **gta_tum_araclar.json:** Tüm araçların verilerini tutan ana veritabanı.
- **garajim.json:** Kullanıcının sahip olduğu araçların listesi.

## Mevcut Özellikler
- [x] **Yapılandırma Sistemi:** `config.json` ile ayarları kolayca değiştirme.
- [x] **Ayarlar Menüsü:** Arayüz üzerinden Tesseract yolu, kısayollar ve OCR alanı düzenleme.
- [x] **Modern UI:** "Ayarlar" penceresi modern (Dark Theme) tasarıma kavuşturuldu.
- [x] **Canlı Tanıma:** Ekrandaki araç ismini okuyup otomatik bilgi kartı açma.
- [x] **HUD (Bilgi Ekranı):** Araç resmi, fiyatı, hızı ve özel etiketler (Zırhlı, Silahlı vb.).
- [x] **Galeri Modu (F11):** Tüm araçları filtreleyip (Sınıf, Marka vb.) inceleme.
- [x] **Garaj Yönetimi (F9):** Araçları garaja ekleme/çıkarma ve toplam garaj değeri hesaplama.
- [x] **Akıllı Rozetler:** "F/P Canavarı", "Lüks", "Roket" gibi otomatik atanan etiketler.
- [x] **Resim Önbellekleme:** İndirilen resimleri RAM'de tutarak performansı artırma.
- [x] **OCR İyileştirmeleri:** Gelişmiş görüntü işleme (OpenCV) ve kontur bazlı hibrit tarama.
- [x] **Seçim Aracı:** Çoklu monitör destekli interaktif bölge seçimi (Taşıma/Boyutlandırma).
- [x] **[NEW]** Ayarlar Penceresi İç İçe Geçme Sorunu Çözümü (QGroupBox) ✅
- [x] **[NEW]** Ayarlar Penceresi Boyutu Artırıldı (600x800) ✅
- [x] **[NEW]** Seçim Aracı Kullanılabilirliği Artırıldı (Kalın Çizgiler, Büyük Tutacaklar) ✅
- [x] **[NEW]** Gelişmiş OCR (CLAHE + Akıllı Zemin Algılama) ✅
- [x] **[NEW]** Performans Modu (Sadece Seçili Satırı Tara) 🚀
- [x] **[NEW]** Veri Çekme Motoru Güncellendi (figure.item-image desteği) ✅
- [x] **[NEW]** Etkileşim Menüsü Desteği (< Araç > Temizliği ve Kara Liste) ✅
- [x] **[NEW]** OCR Renk Hassasiyeti Ayarlandı (Parlaklık Eşiği 110 -> 80) 🎨
- [x] **[NEW]** Akıllı Ayrıştırma (Regex ile `< Araç >` içi okuma) 🧠
- [x] **[NEW]** HUD Takılma Sorunu Giderildi (Hata Kalkanı Eklendi) 🛡️
- [x] **[NEW]** HUD Kayan Yazı (Marquee) Özelliği Eklendi 📜
- [x] **[NEW]** HUD Dinamik Konumlandırma ve Boyutlandırma (Ayarlar Menüsü) 📐
- [x] **[NEW]** Ayarlar Penceresine HUD Konfigürasyonu Entegre Edildi ⚙️
- [x] **[KALITE]** Wildcard Import Kaldırıldı (ui.py: `import *` → Açık import) 🧹
- [x] **[KALITE]** Çift Tanımlı SettingsWindow Silindi (110 satır ölü kod) 🗑️
- [x] **[KALITE]** Bare `except` Düzeltildi (workers.py, database.py) 🛡️
- [x] **[KALITE]** OcrThread.run() Refactored (3 yardımcı metot) 🏗️
- [x] **[KALITE]** Garaj Cache Sistemi (database.py: mtime-bazlı) ⚡
- [x] **[KALITE]** Type Hints Eklendi (tüm dosyalar) 📝
- [x] **[KALITE]** save_garage() Hata Yakalama Eklendi 🔒
- [x] **[KALITE]** config.py: .copy() ile Mutation Koruması 🛡️
- [x] **[HATA]** QPainterPath Import Eksikliği Düzeltildi (Snipper çökme hatası) 💥
- [x] **[HATA]** Cache Referans Paylaşımı Düzeltildi (list() kopyası) 🔒
- [x] **[HATA]** Config Shallow Copy → deepcopy Düzeltildi 🧬
- [x] **[HATA]** F/P Canavarı Badge Mantık Çelişkisi Düzeltildi 🏷️
- [x] **[HATA]** ScrollingLabel İlk Gösterimde Kaymama Sorunu Düzeltildi 📜
- [x] **[NEW]** Araç Kullanım Danışmanı (sınıf sıralaması, sahip olunan araç sayısı, en hızlı karşılaştırma) 🧠
- [x] **[MANTIK]** HUD'da SAHİPSİN rozeti kaldırıldı (menülerde sadece sahip olunan araçlar görünür) 🎮
- [x] **[NEW]** Garaj Analitik Paneli (sınıf dağılımı, rekorlar, eksik sınıflar) 📊
- [x] **[NEW]** Son Görülen Araçlar Geçmişi (zaman damgalı, detay butonu) 🕐
- [x] **[NEW]** Sistem Tepsisi Entegrasyonu (sağ tık: Galeri, Ayarlar, OCR, Çıkış) 🔔
- [x] **[NEW]** history.py Modülü (VehicleHistory sınıfı, istatistikler) 📋
- [x] **[NEW]** OCR Motoru: Tesseract → Windows OCR (winocr) geçişi (30ms tepki süresi) ⚡
- [x] **[NEW]** Akıllı Highlight Tespiti: Parlaklık analizi ile seçili satırı bulma (dinamik HUD) 🔦
- [x] **[NEW]** Durum Göstergesi (Status HUD): Kompakt, oto-gizlenen durum çubuğu (Jarvis & OCR Durumu) 🚥
- [x] **[NEW]** OCR Duraklatma (F10): Kısayol ile taramayı geçici durdurma/başlatma ⏯️
- [x] **[NEW]** Araç Sınıfı Gösterimi: HUD'da araç isminin altında sınıf bilgisi (Sports, Super vb.) 🏎️
- [x] **[NEW]** Fabrika Ayarlarına Dön: Launcher üzerinden tüm ayarları sıfırlama seçeneği 🔄
- [x] **[NEW]** Dinamik Çözünürlük Ölçeklendirme: "Fabrika Ayarlarına Dön" dendiğinde, mevcut ekran çözünürlüğüne göre ayarları otomatik optimize eder (2560x1600 referans alınarak). 📐
- [x] **[NEW]** Launcher HUD Ayarları: Launcher üzerinden artık sadece OCR değil, HUD konumu ve boyutu da ayarlanabiliyor. ⚙️
- [x] **[NEW]** Tek Tıkla Otomatik Ayar: "Otomatik Alan Ayarla" butonu ile diğer ayarlarınızı (kısayollar vb.) bozmadan sadece ekran bölgelerini çözünürlüğünüze göre optimize edebilirsiniz. ✨
- [x] **[NEW]** Akıllı Arayüz Ölçeklendirme: Pencereler (Galeri vb.) ekran boyutunuza göre otomatik olarak %80 oranında açılıyor. (High DPI desteği geçici olarak devre dışı bırakıldı). 🖥️
- [x] **[NEW]** Kesintisiz Pencere Akışı: Galeri'den Ayarlar'a geçerken Galeri gizlenir, Ayarlar'dan çıkınca geri gelir. Arka planda pencere kirliliği oluşmaz. 🔄
- [x] **[NEW]** Gelişmiş Alan Seçimi: OCR veya HUD alanı seçerken ekran tamamen temizlenir. Sadece alt kısımda "Onayla" ve "İptal" butonları görünür. Klavye kullanmaya gerek kalmaz. 🖱️
- [x] **[FIX]** Tüm uyarılara "Karanlık Mod" zorlandı. Artık açılır pencerelerdeki yazılar net bir şekilde okunuyor. 🌙
- [x] **[FIX]** Galeri filtre menülerinin (Araç Sınıfı vb.) renkleri düzenlendi. Artık listeler uygulamanın genel temasıyla (Siyah/Yeşil) uyumlu. 🎨
- [x] **[FIX]** Akıllı Alt-Tab Desteği: Galeri veya Ayarlar açıkken oyundan çıkarsanız (Alt-Tab), pencereler otomatik gizlenir. Oyuna döndüğünüzde kaldığınız yerden geri gelirler. 🔄✨
- [x] **[NEW]** Modifikasyon Atölyesi Filtresi: Galeriye yeni bir filtre eklendi! Artık araçları modifiye edilebildikleri yerlere göre (Örn: Sadece Benny's araçları) listeleyebilirsiniz. 🏎️🛠️
- [x] Pencere normalizasyonu: Pencerelerin ekranın tam ortasında olması ve DPI ölçeklendirme hatalarının giderilmesi. <!-- id: 4 -->
- [x] Dinamik Boyutlandırma: Tüm pencerelerin fare ile kenarlardan büyütülüp küçültülebilmesi ve Galeri grid düzeninin buna göre uyum sağlaması. <!-- id: 5 -->
- [x] Pencere Hafızası: Galeri, Ayarlar ve Launcher pencerelerinin son boyutlarını ve konumlarını hatırlaması. <!-- id: 6 -->

### 🔧 Kritik Stabilite Düzeltmeleri (Commit: 9588ca6)
- [x] **[FIX]** VeriÇek.py eksik fonksiyonlar eklendi (`get_vehicle_details`, `save_data`) 
- [x] **[FIX]** ImageLoaderThread memory leak düzeltildi (thread lifecycle yönetimi)
- [x] **[FIX]** Atomik yazma pattern'i uygulandı (tempfile + os.replace) - veri kaybı koruması
- [x] **[FIX]** QPixmap thread safety düzeltildi (worker thread'de QImage kullanımı)
- [x] **[FIX]** Garaj veritabanı race condition koruması (threading.Lock eklendi)
- [x] **[FIX]** HotkeyThread proper cleanup implementasyonu (keyboard.unhook_all)
- [x] **[FIX]** OCR resource leak düzeltildi (mss context manager, try-finally)
- [x] **[FIX]** Image cache LRU limiti eklendi (max 200 öğe, memory kontrolü)
- [x] **[FIX]** FramelessResizer kod duplikasyonu kaldırıldı (ui_utils.py ortak modül)

### 🎨 UI/UX İyileştirmeleri ve Erişilebilirlik (Commit: 49e8d10)
- [x] **[A11Y]** Klavye navigasyonu desteği (Tab order, Enter/Space aktivasyonu)
- [x] **[A11Y]** Tooltip ve accessible name'ler eklendi (WCAG 2.1 uyumlu)
- [x] **[A11Y]** Renk kontrastı düzeltildi (TEXT_SECONDARY: #B2BEC3, 8.5:1 kontrast)
- [x] **[UX]** Form validasyon feedback (hatalı alan vurgulama, cursor yönlendirme)
- [x] **[UX]** Theme System (Design Tokens: PRIMARY, BACKGROUND, SURFACE renkleri)
- [x] **[UX]** Layout sabitleri (CARD_WIDTH, SPACING_MEDIUM) ve Typography sistemi
- [x] **[PERF]** ScrollingLabel animation optimization (global AnimationManager)
- [x] **[UX]** Gelişmiş sayfalama (İlk/Son sayfa, sayfa input, go_to_page metodu)
- [x] **[UX]** Araç kartlarına sağ tık menüsü (Garaja Ekle/Çıkar, Detayları Gör)
- [x] **[UX]** "Filtreleri Temizle" butonu eklendi

### 🪟 Pencere Yönetimi İyileştirmeleri
- [x] **[FIX]** Launcher minimize/close butonları eklendi (custom title bar, 35px) <!-- Commit: 86fc3c3 -->
- [x] **[FIX]** Pencere boyutları hatırlama sistemi (hideEvent + closeEvent) <!-- Commit: d802b32 -->
- [x] **[FIX]** Galeri resize düzeltmesi (SettingsWindow yaklaşımı uygulandı) <!-- Commit: 4f17fb0, 4e4e0a1 -->
- [x] **[FIX]** Dinamik pencere boyut limitleri (ekranın %90'ı max, multi-monitor desteği) <!-- Commit: 0d56cee -->
- [x] **[FIX]** Mouse button kontrolü (sadece sol tuş ile resize/drag) <!-- Commit: 011a0c4 -->

### 🐛 Kritik UI Hataları Düzeltildi (Commit: 089bea2)
- [x] **[FIX]** Windows OCR exception handling iyileştirildi (spesifik hata tipleri, detaylı mesajlar)
- [x] **[FIX]** Pencere fareyi kendi kendine takip etme sorunu (mouseReleaseEvent flag temizleme)
- [x] **[FIX]** Galeri ilk açılışta tek sütun sorunu (QTimer.singleShot + showEvent timing fix)

### 🧹 Kod Kalitesi ve Bakım
- [x] **[CHORE]** Python cache temizliği (__pycache__, *.pyc git'ten kaldırıldı) <!-- Commit: 2b36932 -->
- [x] **[CHORE]** .gitignore güncellendi (Python bytecode dosyaları eklendi)

### 📦 Profesyonel Kurulum Sistemi (Commit: effda7c)
- [x] **[NEW]** PyInstaller ile tek dosya executable (launcher.exe + main.exe)
- [x] **[NEW]** Inno Setup installer (GtaAsistan_Setup_v1.0.0.exe, ~72MB)
- [x] **[NEW]** Frozen mod desteği (sys.frozen, APP_DIR, mutlak dosya yolları)
- [x] **[NEW]** build.bat: Tek komutla derleme + installer oluşturma
- [x] **[NEW]** Türkçe/İngilizce installer UI
- [x] **[NEW]** Otomatik uninstaller (Program Ekle/Kaldır desteği)
- [x] **[NEW]** Masaüstü kısayolu ve Windows başlangıç seçenekleri
- [x] **[NEW]** requirements.txt: Tüm bağımlılıklar listelendi

### 🛡️ OCR Hata Yönetimi (Commit: 98443bd)
- [x] **[FIX]** Windows OCR dil paketi eksikliğinde graceful fallback
- [x] **[FIX]** AssertionError exception handling (winocr başlatma hatası)
- [x] **[FIX]** Launcher'da subprocess exit code kontrolü (300ms crash detection)
- [x] **[UX]** OCR hatası GUI popup ile bildirim (çözüm adımları dahil)
- [x] **[HATA]** Detaylı hata mesajları (dil paketi eksik, Tesseract yok, vs.)
- [x] **[FIX]** **HUD Kilitlenme Sorunu Giderildi:** F9 ile araç kaydederken yaşanan deadlock (RLock düzeltmesi) giderildi. 🛡️✨


### 🚀 Tam Otomatik Kurulum Sistemi (Commit: c77d952)
- [x] **[NEW]** Tesseract OCR gömülü installer (~60MB, portable)
- [x] **[NEW]** Windows OCR dil paketi otomatik kurulum (admin yetkisi ile)
- [x] **[NEW]** Python paket otomatik kurulumu (pip install winocr)
- [x] **[NEW]** config.json otomatik oluşturma (tesseract_path dahil)
- [x] **[NEW]** Python kontrolü (installer açılışta python --version) ❌ KALDIRILDI
- [x] **[NEW]** Frozen mod tesseract path desteği (_get_default_tesseract_path)
- [x] **[DOC]** INSTALL.md: Kapsamlı kullanıcı ve geliştirici kılavuzu
- [x] **[DOC]** Build süreci dokümantasyonu (Tesseract hazırlık adımları)

### 🎯 Standalone Installer (Commit: a879df9)
- [x] **[FIX]** Python kontrolü kaldırıldı (InitializeSetup fonksiyonu silindi)
- [x] **[FIX]** Hiçbir önkoşul kontrolü yok (tam standalone)
- [x] **[NEW]** README.md: GitHub kullanıcı dostu dokümantasyon
- [x] **[DOC]** INSTALL.md güncellendi ("Python gerekli değil" notu)
- [x] **[NEW]** .gitignore: tesseract_portable/ ve tesseract_setup.exe eklendi

## Yapılacaklar / Geliştirme Önerileri
- [ ] Farklı ekran çözünürlükleri için otomatik ölçeklendirme.
- [ ] Performans optimizasyonu (OCR işlem yükünü azaltma).

## Bilinen Sorunlar
- Çok hızlı değişen ekranlarda OCR bazen yanlış okuma yapabilir.

## Kurallar
1. Kodlar Türkçe yorum satırları içermelidir.
2. Arayüz tasarımı modern ve kullanıcı dostu olmalıdır.
3. Her büyük değişiklik `proje_durumu.md` dosyasına işlenmelidir.
