# main.py
"""GTA Asistan - J.A.R.V.I.S Ana Modül"""
import sys
from collections import OrderedDict
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt
from database import load_vehicle_database, toggle_vehicle_ownership
from workers import OcrThread, HotkeyThread
from ui import OverlayHUD, GalleryWindow, StatusHUD
from config import load_config
from history import VehicleHistory


class LRUCache:
    """LRU (Least Recently Used) cache implementasyonu."""
    def __init__(self, max_size=200):
        self.cache = OrderedDict()
        self.max_size = max_size
    
    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key)
            return self.cache[key]
        return None
    
    def set(self, key, value):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)
    
    def __contains__(self, key):
        return key in self.cache
    
    def __getitem__(self, key):
        return self.get(key)
    
    def __setitem__(self, key, value):
        self.set(key, value)


def create_tray_icon() -> QIcon:
    """Basit bir tray ikonu oluşturur (harici dosya gerekmez)."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#00FF96"))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, 28, 28)
    painter.setPen(QColor("#121212"))
    painter.setFont(QFont("Segoe UI", 14, QFont.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "J")
    painter.end()
    return QIcon(pixmap)


class JarvisApp:
    """Ana uygulama sınıfı. Tüm bileşenleri koordine eder."""
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)  # Tray'de çalışmaya devam etsin
        
        self.cfg = load_config()
        self.search_dict, self.db_data = load_vehicle_database()
        
        # O an hangi araca baktığımızı tutan değişken
        self.current_vehicle_data = None 
        
        # Araç Geçmişi
        self.vehicle_history = VehicleHistory()
        
        if not self.search_dict:
            print("[HATA] Araç veritabanı yüklenemedi! Çıkılıyor...")
            sys.exit()

        self.image_cache = LRUCache(max_size=200)  # LRU cache
        self.hud = OverlayHUD(self.image_cache)
        self.hud.db_data = self.db_data  # Danışman için veritabanı referansı
        self.hud.hide()
        
        self.status_hud = StatusHUD()
        self.status_hud.hide() # Başlangıçta gizli başla, oyun açılınca sinyal ile görünür
        
        self.gallery = GalleryWindow(self.db_data, self.image_cache)
        self.gallery.vehicle_history = self.vehicle_history  # Geçmiş referansı
        self.gallery.hide()

        # İşçi Thread'leri Başlat
        self.ocr_thread = OcrThread(self.search_dict)
        self.ocr_thread.vehicle_found_signal.connect(self.on_vehicle_found)
        self.ocr_thread.hide_hud_signal.connect(self.hud.hide) 
        self.ocr_thread.gta_window_active_signal.connect(self.toggle_windows_visibility) # YENİ: Akıllı Görünürlük Yönetimi
        self.ocr_thread.start()
        
        self.hotkey_thread = HotkeyThread()
        self.hotkey_thread.toggle_gallery_signal.connect(self.toggle_gallery)
        self.hotkey_thread.toggle_ownership_signal.connect(self.toggle_ownership)
        self.hotkey_thread.toggle_ocr_signal.connect(self.toggle_ocr)
        self.hotkey_thread.start()
        
        # Sistem Tepsisi
        self.setup_system_tray()
        
        print("[SİSTEM] J.A.R.V.I.S Asistanı Aktif!")
        
        hk_gallery = self.cfg["hotkeys"].get("toggle_gallery", "f11")
        hk_ownership = self.cfg["hotkeys"].get("toggle_ownership", "f9")
        print(f"[BİLGİ] Galeri: {hk_gallery.upper()} | Garaja Ekle/Çıkar: {hk_ownership.upper()}")
        print("[BİLGİ] Sistem tepsisine küçültüldü (saat yanındaki ikon).")

        
        # Görünürlük durumlarını takip etmek için
        self.gallery_was_visible = False
        self.settings_was_visible = False

    def setup_system_tray(self):
        """Sistem tepsisi ikonunu ve menüsünü oluşturur."""
        self.tray_icon = QSystemTrayIcon(create_tray_icon(), self.app)
        
        tray_menu = QMenu()
        tray_menu.setStyleSheet("""
            QMenu { background: #2d3436; color: white; font-size: 10pt; padding: 5px; }
            QMenu::item { padding: 8px 20px; }
            QMenu::item:selected { background: #00FF96; color: black; }
        """)
        
        # Galeri Aç
        action_gallery = QAction("🏎️ Galeri Aç", self.app)
        action_gallery.triggered.connect(self.toggle_gallery)
        tray_menu.addAction(action_gallery)
        
        # Ayarlar
        action_settings = QAction("⚙️ Ayarlar", self.app)
        action_settings.triggered.connect(self.open_settings)
        tray_menu.addAction(action_settings)
        
        tray_menu.addSeparator()
        
        # OCR Durdur/Başlat
        self.action_ocr_toggle = QAction("⏸️ OCR Durdur", self.app)
        self.action_ocr_toggle.triggered.connect(self.toggle_ocr)
        tray_menu.addAction(self.action_ocr_toggle)
        
        tray_menu.addSeparator()
        
        # Çıkış
        action_exit = QAction("❌ Çıkış", self.app)
        action_exit.triggered.connect(self.quit_app)
        tray_menu.addAction(action_exit)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("J.A.R.V.I.S - GTA Asistan")
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()
    
    def on_tray_activated(self, reason):
        """Tray ikonuna çift tıklanınca galeriyi aç."""
        if reason == QSystemTrayIcon.DoubleClick:
            self.toggle_gallery()
    
    def toggle_ocr(self):
        """OCR thread'ini durdurur/başlatır."""
        self.ocr_thread.paused = not self.ocr_thread.paused
        
        if self.ocr_thread.paused:
            self.action_ocr_toggle.setText("▶️ OCR Başlat")
            self.hud.hide()
            self.status_hud.update_status(False)
            print("[SİSTEM] OCR durduruldu (PAUSED).")
        else:
            self.action_ocr_toggle.setText("⏸️ OCR Durdur")
            self.status_hud.update_status(True)
            print("[SİSTEM] OCR devam ettiriliyor.")
    
    def open_settings(self):
        """Ayarlar penceresini açar."""
        if hasattr(self.gallery, 'settings_window'):
            self.gallery.settings_window.load_settings()
            self.gallery.settings_window.show()
            
    def toggle_windows_visibility(self, gta_active: bool):
        """
        Oyun alta atıldığında (Alt-Tab) asistan pencerelerini gizle,
        oyun geri gelince eski durumlarına döndür.
        """
        # Status HUD sadece GTA aktifken görünmeli (Bizim penceremiz aktif olsa bile HUD'a gerek yok)
        self.status_hud.setVisible(gta_active)
        
        # Eğer GTA aktif değilse, ama kullanıcı BİZİM penceremize (Galeri/Ayarlar) tıkladıysa gizleme!
        app_highlighted = (self.app.activeWindow() is not None)
        
        if not gta_active and not app_highlighted:
            # Hem GTA hem Biz pasifiz -> Başka kroma geçti -> GİZLE
            
            # Galeri açık mıydı?
            if self.gallery.isVisible():
                self.gallery_was_visible = True
                self.gallery.hide()
            
            # Ayarlar açık mıydı?
            if hasattr(self.gallery, 'settings_window') and self.gallery.settings_window.isVisible():
                self.settings_was_visible = True
                self.gallery.settings_window.hide()
                
        elif gta_active or app_highlighted:
            # Oyun geri geldi VEYA kullanıcı direkt asistan penceresine tıkladı
            if self.gallery_was_visible:
                self.gallery.show()
                self.gallery_was_visible = False
            
            if self.settings_was_visible and hasattr(self.gallery, 'settings_window'):
                self.gallery.settings_window.show()
                self.settings_was_visible = False
    
    def quit_app(self):
        """Uygulamadan tamamen çıkar. Thread'leri düzgün kapatır."""
        print("[SİSTEM] Uygulama kapatılıyor...")
        
        # OCR thread'ini durdur
        self.ocr_thread.running = False
        self.ocr_thread.wait(2000)  # 2 saniye bekle
        
        # Hotkey thread'ini durdur
        self.hotkey_thread.stop()
        self.hotkey_thread.wait(2000)  # 2 saniye bekle
        
        # Tray icon'u gizle
        self.tray_icon.hide()
        
        # Uygulamayı kapat
        self.app.quit()

    def on_vehicle_found(self, vehicle_data: dict) -> None:
        """OCR bir araç bulduğunda çalışır."""
        self.current_vehicle_data = vehicle_data
        self.hud.update_ui(vehicle_data)
        
        # Geçmişe kaydet
        vehicle_name = vehicle_data.get("Vehicle Name", "")
        if vehicle_name:
            self.vehicle_history.add(vehicle_name, vehicle_data)

    def toggle_gallery(self) -> None:
        """Galeri penceresini açar/kapatır."""
        if self.gallery.isVisible():
            self.gallery.hide()
        else:
            self.gallery.stacked_widget.setCurrentIndex(0)
            self.gallery.show()
            self.gallery.activateWindow()
            self.gallery.setFocus()

    def toggle_ownership(self) -> None:
        """Aktif aracı garaja ekler/çıkarır."""
        if self.current_vehicle_data:
            name = self.current_vehicle_data.get("Vehicle Name")
            if name:
                is_added = toggle_vehicle_ownership(name)
                state = "EKLENDİ" if is_added else "ÇIKARILDI"
                print(f"[GARAJ] {name} -> {state}")
                
                # Arayüzü anında güncelle
                self.hud.update_ui(self.current_vehicle_data)

    def run(self) -> None:
        """Uygulamayı başlatır."""
        sys.exit(self.app.exec_())


if __name__ == "__main__":
    jarvis = JarvisApp()
    jarvis.run()