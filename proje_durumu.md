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

## Yapılacaklar / Geliştirme Önerileri
- [ ] Farklı ekran çözünürlükleri için otomatik ölçeklendirme.
- [ ] Performans optimizasyonu (OCR işlem yükünü azaltma).

## Bilinen Sorunlar
- Çok hızlı değişen ekranlarda OCR bazen yanlış okuma yapabilir.

## Kurallar
1. Kodlar Türkçe yorum satırları içermelidir.
2. Arayüz tasarımı modern ve kullanıcı dostu olmalıdır.
3. Her büyük değişiklik `proje_durumu.md` dosyasına işlenmelidir.
