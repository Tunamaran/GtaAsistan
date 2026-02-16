import sys
import os
import subprocess
import json
from config import APP_DIR
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTabWidget, 
                             QTextEdit, QLineEdit, QFormLayout, QGroupBox, 
                             QMessageBox, QProgressBar, QSpacerItem, QSizePolicy,
                             QCheckBox, QSystemTrayIcon, QMenu, QAction)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor
import ctypes
import time

# Config modülünü yükle
import config

# VeriÇek modülünü import etmeyi dene
try:
    import VeriÇek as data_updater
except ImportError:
    data_updater = None

# Stil Dosyası
STYLESHEET = """
QMainWindow {
    background-color: #1e1e1e;
}
QWidget {
    color: #ffffff;
    font-family: 'Segoe UI', sans-serif;
    font-size: 14px;
}
QTabWidget::pane {
    border: 1px solid #3d3d3d;
    background-color: #252526;
}
QTabBar::tab {
    background-color: #2d2d30;
    color: #cccccc;
    padding: 10px 20px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}
QTabBar::tab:selected {
    background-color: #3e3e42;
    color: #ffffff;
    border-bottom: 2px solid #007acc;
}
QPushButton {
    background-color: #0e639c;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #1177bb;
}
QPushButton:pressed {
    background-color: #094770;
}
QLineEdit {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    color: white;
    padding: 4px;
    border-radius: 2px;
}
QTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #3d3d3d;
    color: #d4d4d4;
    font-family: 'Consolas', monospace;
}
QProgressBar {
    border: 1px solid #3d3d3d;
    border-radius: 2px;
    text-align: center;
    background-color: #2d2d2d;
}
QProgressBar::chunk {
    background-color: #0e639c;
}
QMessageBox {
    background-color: #1e1e1e;
}
QMessageBox QLabel {
    color: white;
}
QMessageBox QPushButton {
    background-color: #0e639c;
    color: white;
    border: none;
    padding: 6px 15px;
    border-radius: 4px;
}
QMessageBox QPushButton:hover {
    background-color: #1177bb;
}
"""

class UpdateThread(QThread):
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    
    def __init__(self, incremental=False):
        super().__init__()
        self.incremental = incremental

    def run(self):
        if data_updater:
            # GUI callback üzerinden loglama
            try:
                data_updater.run_update(self.log_callback, self.incremental)
            except Exception as e:
                self.log_signal.emit(f"Kritik Hata: {str(e)}")
        else:
            self.log_signal.emit("VeriÇek modülü bulunamadı!")
        self.finished_signal.emit()
        
    def log_callback(self, msg):
        self.log_signal.emit(str(msg))

class AutoPilotThread(QThread):
    game_started = pyqtSignal()
    game_stopped = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.running = True
        self.game_running = False

    def run(self):
        while self.running:
            # GTA 5 Pencere Kontrolü (Windows API)
            hwnd = ctypes.windll.user32.FindWindowW(None, "Grand Theft Auto V")
            
            if hwnd != 0 and not self.game_running:
                # Oyun yeni açıldı
                self.game_running = True
                self.game_started.emit()
            elif hwnd == 0 and self.game_running:
                # Oyun kapandı
                self.game_running = False
                self.game_stopped.emit()
            
            time.sleep(3) # 3 saniyede bir kontrol et

    def stop(self):
        self.running = False
        self.wait()

# ==========================================
# FRAMELESS RESIZER (Çerçevesiz Pencereler İçin)
# ==========================================
class FramelessResizer:
    def __init__(self, window):
        self.window = window
        self.window.setMouseTracking(True)
        self.margin = 10
        self._is_resizing = False
        self._is_dragging = False
        self._drag_pos = None
        self._resize_dir = None

    def handle_mouse_press(self, event):
        if event.button() == Qt.LeftButton:
            pos = event.pos()
            edge = self.get_edge(pos)
            if edge:
                self._is_resizing = True
                self._resize_dir = edge
            else:
                self._is_dragging = True
                self._drag_pos = event.globalPos() - self.window.frameGeometry().topLeft()
            event.accept()

    def handle_mouse_move(self, event):
        pos = event.pos()
        if self._is_resizing:
            self.resize_window(event.globalPos())
        elif self._is_dragging:
            self.window.move(event.globalPos() - self._drag_pos)
        else:
            edge = self.get_edge(pos)
            self.update_cursor(edge)

    def handle_mouse_release(self, event):
        self._is_resizing = False
        self._is_dragging = False
        self.window.unsetCursor()

    def get_edge(self, pos):
        w, h = self.window.width(), self.window.height()
        x, y = pos.x(), pos.y()
        m = self.margin
        
        edge = ""
        if y < m: edge += "T"
        elif y > h - m: edge += "B"
        if x < m: edge += "L"
        elif x > w - m: edge += "R"
        return edge if edge else None

    def update_cursor(self, edge):
        if edge in ("TL", "BR"): self.window.setCursor(Qt.SizeFDiagCursor)
        elif edge in ("TR", "BL"): self.window.setCursor(Qt.SizeBDiagCursor)
        elif edge in ("T", "B"): self.window.setCursor(Qt.SizeVerCursor)
        elif edge in ("L", "R"): self.window.setCursor(Qt.SizeHorCursor)
        else: self.window.unsetCursor()

    def resize_window(self, global_pos):
        # QMainWindow için frameGeometry kullanmak daha sağlıklı olabilir
        rect = self.window.geometry()
        m_pos = global_pos
        
        if "L" in self._resize_dir: rect.setLeft(m_pos.x())
        if "R" in self._resize_dir: rect.setRight(m_pos.x())
        if "T" in self._resize_dir: rect.setTop(m_pos.y())
        if "B" in self._resize_dir: rect.setBottom(m_pos.y())
        
        if rect.width() > 400 and rect.height() > 300:
            self.window.setGeometry(rect)

class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GTA Asistan Launcher")
        
        # 1. Ekran boyutlarını al
        screen = QApplication.primaryScreen().availableGeometry()
        
        # 2. Minimum ve maksimum boyutları hesapla
        min_width, min_height = 500, 400
        max_width = int(screen.width() * 0.9)
        max_height = int(screen.height() * 0.9)
        
        self.setMinimumSize(min_width, min_height)
        self.setMaximumSize(max_width, max_height)
        
        # 3. Kayıtlı Geometriyi Al veya Varsayılanı Hesapla
        cfg = config.load_config()
        geom = cfg.get("ui_geometry", {}).get("LauncherWindow", {})
        
        # Varsayılan boyut
        default_width = min(700, int(screen.width() * 0.5))
        default_height = min(500, int(screen.height() * 0.6))
        
        width = geom.get("width", default_width)
        height = geom.get("height", default_height)
        
        # Boyutları limitlere göre kısıtla
        width = max(min_width, min(width, max_width))
        height = max(min_height, min(height, max_height))
        
        # 4. Pozisyon hesapla (her zaman ekran içinde)
        if geom.get("x", -1) != -1:
            left = geom["x"]
            top = geom["y"]
            
            # Pencere ekran dışına çıkmasın
            if left + width > screen.x() + screen.width():
                left = screen.x() + screen.width() - width - 20
            if top + height > screen.y() + screen.height():
                top = screen.y() + screen.height() - height - 20
            if left < screen.x():
                left = screen.x() + 20
            if top < screen.y():
                top = screen.y() + 20
        else:
            # İlk açılışta ekranın ortasında
            left = screen.x() + (screen.width() - width) // 2
            top = screen.y() + (screen.height() - height) // 2
        
        self.setGeometry(left, top, width, height)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setStyleSheet(STYLESHEET)
        
        # Resizer'ı başlat
        self.resizer = FramelessResizer(self)
        
        # Config yükle
        self.cfg = config.load_config()
        self.update_thread = None
        self.assistant_process = None
        
        # Auto-Pilot Thread
        self.autopilot_thread = AutoPilotThread()
        self.autopilot_thread.game_started.connect(self.on_game_started)
        self.autopilot_thread.game_stopped.connect(self.on_game_stopped)
        
        # Tray Icon Kurulumu
        self.init_tray()
        
        self.init_ui()
        
        # Config'den durumu yükle
        if self.cfg.get("autopilot", False):
            self.autopilot_chk.setChecked(True)
            self.toggle_autopilot(True)

    def closeEvent(self, event):
        """Pencere kapandığında boyut ve konumu kaydet."""
        self._save_geometry()
        
        # Autopilot kontrolü
        if self.autopilot_chk.isChecked():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Auto-Pilot Aktif",
                "Launcher arka planda GTA 5'i bekliyor.\nÇıkmak için sistem tepsisini kullanın.",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.quit_app()
    
    def hideEvent(self, event):
        """Pencere gizlendiğinde de boyut ve konumu kaydet."""
        self._save_geometry()
        super().hideEvent(event)
    
    def _save_geometry(self):
        """Pencere geometrisini config'e kaydet."""
        cfg = config.load_config()
        if "ui_geometry" not in cfg: 
            cfg["ui_geometry"] = {}
        
        geom = self.geometry()
        cfg["ui_geometry"]["LauncherWindow"] = {
            "width": geom.width(),
            "height": geom.height(),
            "x": geom.x(),
            "y": geom.y()
        }
        config.save_config(cfg)

    def mousePressEvent(self, event):
        # Sadece sol tuş ile resize/drag
        if event.button() == Qt.LeftButton:
            self.resizer.handle_mouse_press(event)
        else:
            # Sağ tuş veya diğer butonlar için varsayılan davranış
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.resizer.handle_mouse_move(event)

    def mouseReleaseEvent(self, event):
        # Her zaman resizer'ı bilgilendir (flag temizleme için)
        self.resizer.handle_mouse_release(event)
        if event.button() != Qt.LeftButton:
            super().mouseReleaseEvent(event)
    
    # Title bar drag metodları
    def _title_bar_press(self, event):
        """Title bar'a tıklandığında pencereyi taşımaya başla"""
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def _title_bar_move(self, event):
        """Title bar sürüklenirken pencereyi taşı"""
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
    
    def _title_bar_release(self, event):
        """Title bar bırakıldığında drag'i bitir"""
        self._drag_pos = None
        event.accept()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.setMinimumSize(500, 400) # Minimum boyut sınırı
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)  # Tam ekran title bar için
        layout.setSpacing(0)
        
        # === CUSTOM TITLE BAR ===
        title_bar = QWidget()
        title_bar.setFixedHeight(35)
        title_bar.setStyleSheet("""
            QWidget {
                background-color: #2d2d30;
                border-bottom: 1px solid #3d3d3d;
            }
        """)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.setContentsMargins(10, 0, 5, 0)
        title_bar_layout.setSpacing(0)
        
        # Başlık metni (draggable alan)
        self.title_label = QLabel("🚗 GTA Asistan Launcher")
        self.title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.title_label.setStyleSheet("color: #cccccc; background: transparent; border: none;")
        title_bar_layout.addWidget(self.title_label)
        title_bar_layout.addStretch()
        
        # Minimize butonu
        self.min_btn = QPushButton("—")
        self.min_btn.setFixedSize(45, 35)
        self.min_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #cccccc;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3e3e42;
            }
        """)
        self.min_btn.clicked.connect(self.showMinimized)
        title_bar_layout.addWidget(self.min_btn)
        
        # Close butonu
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(45, 35)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #cccccc;
                border: none;
                font-size: 22px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e81123;
                color: white;
            }
        """)
        self.close_btn.clicked.connect(self.close)
        title_bar_layout.addWidget(self.close_btn)
        
        layout.addWidget(title_bar)
        
        # Drag desteği için title bar event handling
        self._drag_pos = None
        title_bar.mousePressEvent = self._title_bar_press
        title_bar.mouseMoveEvent = self._title_bar_move
        title_bar.mouseReleaseEvent = self._title_bar_release
        self.title_label.mousePressEvent = self._title_bar_press
        self.title_label.mouseMoveEvent = self._title_bar_move
        self.title_label.mouseReleaseEvent = self._title_bar_release
        
        # === ANA İÇERİK ===
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Başlık ve Versiyon
        header_layout = QHBoxLayout()
        title_lbl = QLabel("GTA Asistan Yöneticisi")
        title_lbl.setFont(QFont("Segoe UI", 20, QFont.Bold))
        header_layout.addWidget(title_lbl)
        content_layout.addLayout(header_layout)
        
        # Sekmeler
        self.tabs = QTabWidget()
        content_layout.addWidget(self.tabs)
        
        layout.addWidget(content_widget)
        
        # Sekme İçeriklerini Oluştur
        data_tab = QWidget()
        self.setup_data_tab(data_tab)
        self.tabs.addTab(data_tab, "Veri & Başlat")
        
        settings_tab = QWidget()
        self.setup_settings_tab(settings_tab)
        self.tabs.addTab(settings_tab, "Ayarlar")
        
    def setup_data_tab(self, tab):
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Auto-Pilot Checkbox (En Üstte)
        self.autopilot_chk = QCheckBox("Auto-Pilot Modu (GTA 5 Açılınca Otomatik Başlat)")
        self.autopilot_chk.setToolTip("İşaretliyse: Launcher kapanmaz, tepsiye küçülür ve oyunu bekler.")
        self.autopilot_chk.setStyleSheet("QCheckBox { font-weight: bold; color: #4CAF50; padding: 5px; border: 1px solid #3d3d3d; border-radius: 4px; }")
        self.autopilot_chk.toggled.connect(self.toggle_autopilot)
        layout.addWidget(self.autopilot_chk)
        
        # Durum Kartı
        status_group = QGroupBox("Sistem Durumu")
        status_layout = QVBoxLayout(status_group)
        
        self.status_lbl = QLabel("Durum Kontrol Ediliyor...")
        self.status_lbl.setFont(QFont("Segoe UI", 12))
        self.vehicle_count_lbl = QLabel("")
        
        status_layout.addWidget(self.status_lbl)
        status_layout.addWidget(self.vehicle_count_lbl)
        layout.addWidget(status_group)
        
        self.check_status()
        
        # İşlem Butonları Yatay
        btn_layout = QHBoxLayout()
        
        self.update_btn = QPushButton("Verileri Güncelle (İnternetten İndir)")
        self.update_btn.clicked.connect(self.start_update)
        self.update_btn.setMinimumHeight(40)
        
        start_btn = QPushButton("ASİSTANI BAŞLAT") 
        # ... (Start button code lines 163-167 skipped/assumed same) ...
        # Wait, I cannot skip lines inside ReplacementContent easily.
        # I'll rewrite the whole block or split into chunks.
        # Chunk strategy: Insert checkbox before buttons.
        
        # Checkbox
        self.incremental_chk = QCheckBox("Sadece eksik/yeni araçları indir (Hızlı Mod)")
        self.incremental_chk.setChecked(True)
        self.incremental_chk.setToolTip("İşaretliyse: Sadece veritabanında olmayan araçları indirir.\nİşaretli Değilse: Tüm veritabanını silip sıfırdan indirir.")
        self.incremental_chk.setStyleSheet("QCheckBox { color: #cccccc; padding: 5px; } QCheckBox::indicator { width: 18px; height: 18px; }")
        layout.addWidget(self.incremental_chk)

        # İşlem Butonları Yatay
        btn_layout = QHBoxLayout()
        
        self.update_btn = QPushButton("Verileri Güncelle (İnternetten İndir)")
        self.update_btn.clicked.connect(self.start_update)
        self.update_btn.setMinimumHeight(40)
        
        start_btn = QPushButton("ASİSTANI BAŞLAT") 
        start_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        start_btn.setMinimumHeight(40)
        start_btn.setStyleSheet("background-color: #2ea043; color: white; border-radius: 4px;")
        start_btn.clicked.connect(self.start_assistant)
        
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(start_btn)
        layout.addLayout(btn_layout)
        
        # Log Alanı
        layout.addWidget(QLabel("İşlem Kayıtları:"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # Progress Bar (Gizli)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def setup_settings_tab(self, tab):
        layout = QFormLayout(tab)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        layout.addRow(QLabel("OCR Arama Bölgesi (Sol Üst Menü):"))
        
        ocr = self.cfg.get("ocr_region", {})
        self.input_top = QLineEdit(str(ocr.get("top", 0)))
        self.input_left = QLineEdit(str(ocr.get("left", 0)))
        self.input_width = QLineEdit(str(ocr.get("width", 500)))
        self.input_height = QLineEdit(str(ocr.get("height", 800)))
        
        layout.addRow("Top (Y):", self.input_top)
        layout.addRow("Left (X):", self.input_left)
        layout.addRow("Width (Genişlik):", self.input_width)
        layout.addRow("Height (Yükseklik):", self.input_height)
        
        layout.addRow(QLabel("")) # Spacer

        layout.addRow(QLabel("HUD Gösterge Bölgesi (Sağ Panel):"))
        
        hud = self.cfg.get("hud_region", {})
        self.input_hud_top = QLineEdit(str(hud.get("top", 40)))
        self.input_hud_left = QLineEdit(str(hud.get("left", 1325)))
        self.input_hud_width = QLineEdit(str(hud.get("width", 1215)))
        self.input_hud_height = QLineEdit(str(hud.get("height", 1510)))
        
        layout.addRow("Top (Y):", self.input_hud_top)
        layout.addRow("Left (X):", self.input_hud_left)
        layout.addRow("Width (Genişlik):", self.input_hud_width)
        layout.addRow("Height (Yükseklik):", self.input_hud_height)
        
        layout.addRow(QLabel("")) # Spacer
        
        layout.addRow(QLabel("Kısayol Tuşları:"))
        hk = self.cfg.get("hotkeys", {})
        self.input_hk_gallery = QLineEdit(hk.get("toggle_gallery", "f11"))
        self.input_hk_own = QLineEdit(hk.get("toggle_ownership", "f9"))
        
        layout.addRow("Galeri (Aç/Kapa):", self.input_hk_gallery)
        layout.addRow("Sahiplik (Ekle/Çıkar):", self.input_hk_own)
        
        layout.addRow(QLabel("")) # Spacer
        
        
        layout.addRow(QLabel("")) # Spacer
        
        # Windows Başlangıç Ayarı
        self.startup_chk = QCheckBox("Windows Başlangıcında Çalıştır")
        self.startup_chk.setChecked(self.check_startup_status())
        self.startup_chk.toggled.connect(self.toggle_startup)
        layout.addRow(self.startup_chk)
        
        save_btn = QPushButton("Ayarları Kaydet")
        save_btn.setMinimumHeight(35)
        save_btn.clicked.connect(self.save_settings)
        layout.addRow(save_btn)

        auto_scale_btn = QPushButton("Otomatik Alan Ayarla (Çözünürlüğe Göre)")
        auto_scale_btn.setMinimumHeight(30)
        auto_scale_btn.setStyleSheet("background-color: #0984e3; color: white;")
        auto_scale_btn.clicked.connect(self.auto_scale_settings)
        layout.addRow(auto_scale_btn)

        reset_btn = QPushButton("Fabrika Ayarlarına Dön")
        reset_btn.setMinimumHeight(30)
        reset_btn.setStyleSheet("background-color: #d63031; color: white;")
        reset_btn.clicked.connect(self.reset_settings)
        layout.addRow(reset_btn)

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QApplication.style().SP_ComputerIcon))
        
        tray_menu = QMenu()
        show_action = QAction("Göster", self)
        show_action.triggered.connect(self.show_normal)
        quit_action = QAction("Kapat", self)
        quit_action.triggered.connect(self.quit_app)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_click)
        self.tray_icon.show()

    def on_tray_click(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_normal()

    def show_normal(self):
        self.show()
        self.setWindowState(Qt.WindowNoState)
        self.activateWindow()

    def quit_app(self):
        self.autopilot_thread.stop()
        if self.assistant_process:
            self.assistant_process.terminate()
        QApplication.quit()

    def closeEvent(self, event):
        if self.autopilot_chk.isChecked():
            event.ignore()
            self.hide()
            self.tray_icon.showMessage(
                "Auto-Pilot Aktif",
                "Launcher arka planda GTA 5'i bekliyor.\nÇıkmak için sistem tepsisini kullanın.",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.quit_app()

    def changeEvent(self, event):
        if event.type() == 105: # QEvent.WindowStateChange
            if self.windowState() & Qt.WindowMinimized:
                # Küçültme butonuna basıldı -> Tepsiye gönder
                event.ignore()
                self.hide()
                self.tray_icon.showMessage(
                    "Sistem Tepsisine Küçültüldü", 
                    "Uygulama arka planda çalışıyor.",
                    QSystemTrayIcon.Information, 
                    1000
                )
        super().changeEvent(event)

    def toggle_autopilot(self, checked):
        self.cfg["autopilot"] = checked
        config.save_config(self.cfg)
        
        if checked:
            if not self.autopilot_thread.isRunning():
                self.autopilot_thread.start()
        else:
            self.autopilot_thread.stop()

    def on_game_started(self):
        if not self.assistant_process or self.assistant_process.poll() is not None: 
            self.log_text.append("🎮 GTA 5 Algılandı! Asistan başlatılıyor...")
            # Launcher ikonunu gizle (Asistan'ın ikonu gelecek)
            self.tray_icon.hide()
            self.start_assistant(hide_launcher=False)

    def on_game_stopped(self):
        if self.assistant_process:
            self.log_text.append("🛑 Oyun kapandı. Asistan kapatılıyor...")
            self.assistant_process.terminate()
            self.assistant_process = None
            # Launcher ikonunu geri getir
            self.tray_icon.show()
            self.tray_icon.showMessage("GTA Asistan", "Asistan kapandı, Launcher beklemede.", QSystemTrayIcon.Information, 2000)

    def check_startup_status(self):
        startup_path = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup', 'GTA_Asistan_Launcher.lnk')
        return os.path.exists(startup_path)

    def toggle_startup(self, checked):
        startup_path = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup', 'GTA_Asistan_Launcher.lnk')
        
        if getattr(sys, 'frozen', False):
            target_exe = os.path.join(APP_DIR, "launcher.exe")
            working_dir = APP_DIR
        else:
            python_exe = sys.executable
            pythonw = python_exe.replace("python.exe", "pythonw.exe")
            if not os.path.exists(pythonw): pythonw = python_exe
            target_exe = pythonw
            working_dir = APP_DIR
        
        if checked:
            if getattr(sys, 'frozen', False):
                cmd = f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{startup_path}");$s.TargetPath="{target_exe}";$s.WorkingDirectory="{working_dir}";$s.Save()'
            else:
                launcher_path = os.path.join(APP_DIR, "launcher.py")
                cmd = f'$s=(New-Object -COM WScript.Shell).CreateShortcut("{startup_path}");$s.TargetPath="{target_exe}";$s.Arguments="{launcher_path}";$s.WorkingDirectory="{working_dir}";$s.Save()'
            subprocess.run(["powershell", "-Command", cmd], capture_output=True)
            QMessageBox.information(self, "Bilgi", "Windows başlangıcına eklendi.")
        else:
            if os.path.exists(startup_path):
                os.remove(startup_path)
                QMessageBox.information(self, "Bilgi", "Windows başlangıcından kaldırıldı.")

    def check_status(self):
        db_file = os.path.join(APP_DIR, "gta_tum_araclar.json")
        if os.path.exists(db_file):
            try:
                with open(db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    count = len(data)
                    self.status_lbl.setText("✅ Veritabanı Hazır")
                    self.status_lbl.setStyleSheet("color: #4CAF50; font-weight: bold;")
                    self.vehicle_count_lbl.setText(f"{count} adet araç kaydı mevcut.")
            except:
                self.status_lbl.setText("❌ Veritabanı Okunamadı!")
                self.status_lbl.setStyleSheet("color: #F44336; font-weight: bold;")
        else:
            self.status_lbl.setText("⚠️ Veritabanı Bulunamadı!")
            self.status_lbl.setStyleSheet("color: #FFC107; font-weight: bold;")
            self.vehicle_count_lbl.setText("Lütfen 'Verileri Güncelle' butonunu kullanın.")

    def start_update(self):
        if not data_updater:
            QMessageBox.critical(self, "Hata", "VeriÇek modülü yüklenemedi!")
            return
            
        self.update_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.log_text.clear()
        
        incremental = self.incremental_chk.isChecked()
        mode_str = "HIZLI" if incremental else "TAM"
        self.log_text.append(f"🔄 Güncelleme başlatılıyor ({mode_str} MOD)... Lütfen bekleyin.")
        
        self.update_thread = UpdateThread(incremental)
        self.update_thread.log_signal.connect(self.append_log)
        self.update_thread.finished_signal.connect(self.on_update_finished)
        self.update_thread.start()

    def append_log(self, msg):
        self.log_text.append(msg)
        sb = self.log_text.verticalScrollBar()
        sb.setValue(sb.maximum())

    def on_update_finished(self):
        self.update_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.log_text.append("\n✅ İşlem tamamlandı.")
        self.check_status()
        QMessageBox.information(self, "Bilgi", "Veri güncelleme işlemi başarıyla bitti.")

    def save_settings(self):
        """Ayarları kaydet - hatalı alanları vurgula"""
        # Önce tüm alanların stilini sıfırla
        input_fields = [
            self.input_top, self.input_left, self.input_width, self.input_height,
            self.input_hud_top, self.input_hud_left, self.input_hud_width, self.input_hud_height
        ]
        for field in input_fields:
            field.setStyleSheet("")  # Stil sıfırla
        
        error_field = None
        error_msg = ""
        
        try:
            # OCR Region validation
            try:
                self.cfg["ocr_region"]["top"] = int(self.input_top.text())
            except ValueError:
                error_field = self.input_top
                error_msg = "OCR Top değeri geçerli bir sayı olmalıdır"
                raise
            
            try:
                self.cfg["ocr_region"]["left"] = int(self.input_left.text())
            except ValueError:
                error_field = self.input_left
                error_msg = "OCR Left değeri geçerli bir sayı olmalıdır"
                raise
            
            try:
                self.cfg["ocr_region"]["width"] = int(self.input_width.text())
            except ValueError:
                error_field = self.input_width
                error_msg = "OCR Width değeri geçerli bir sayı olmalıdır"
                raise
            
            try:
                self.cfg["ocr_region"]["height"] = int(self.input_height.text())
            except ValueError:
                error_field = self.input_height
                error_msg = "OCR Height değeri geçerli bir sayı olmalıdır"
                raise
            
            # HUD Region Key Check (Eski configlerde olmayabilir)
            if "hud_region" not in self.cfg: 
                self.cfg["hud_region"] = {}
            
            try:
                self.cfg["hud_region"]["top"] = int(self.input_hud_top.text())
            except ValueError:
                error_field = self.input_hud_top
                error_msg = "HUD Top değeri geçerli bir sayı olmalıdır"
                raise
            
            try:
                self.cfg["hud_region"]["left"] = int(self.input_hud_left.text())
            except ValueError:
                error_field = self.input_hud_left
                error_msg = "HUD Left değeri geçerli bir sayı olmalıdır"
                raise
            
            try:
                self.cfg["hud_region"]["width"] = int(self.input_hud_width.text())
            except ValueError:
                error_field = self.input_hud_width
                error_msg = "HUD Width değeri geçerli bir sayı olmalıdır"
                raise
            
            try:
                self.cfg["hud_region"]["height"] = int(self.input_hud_height.text())
            except ValueError:
                error_field = self.input_hud_height
                error_msg = "HUD Height değeri geçerli bir sayı olmalıdır"
                raise
            
            self.cfg["hotkeys"]["toggle_gallery"] = self.input_hk_gallery.text()
            self.cfg["hotkeys"]["toggle_ownership"] = self.input_hk_own.text()
            
            config.save_config(self.cfg)
            QMessageBox.information(self, "Başarılı", "Ayarlar kaydedildi.")
            
        except ValueError:
            # Hatalı alanı vurgula
            if error_field:
                error_field.setStyleSheet(f"""
                    QLineEdit {{
                        border: 2px solid #d63031;
                        background: rgba(214, 48, 49, 0.1);
                    }}
                """)
                error_field.setFocus()
            QMessageBox.warning(self, "Hata", error_msg or "Lütfen geçerli değerler giriniz.")

    def auto_scale_settings(self):
        try:
            defaults = config.get_scaled_default_config()
            
            # Sadece bölge ayarlarını güncelle
            self.cfg["ocr_region"] = defaults["ocr_region"]
            self.cfg["hud_region"] = defaults["hud_region"]
            
            # UI Güncelle
            ocr = self.cfg["ocr_region"]
            self.input_top.setText(str(ocr.get("top")))
            self.input_left.setText(str(ocr.get("left")))
            self.input_width.setText(str(ocr.get("width")))
            self.input_height.setText(str(ocr.get("height")))
            
            hud = self.cfg["hud_region"]
            self.input_hud_top.setText(str(hud.get("top")))
            self.input_hud_left.setText(str(hud.get("left")))
            self.input_hud_width.setText(str(hud.get("width")))
            self.input_hud_height.setText(str(hud.get("height")))
            
            QMessageBox.information(self, "Bilgi", "Alanlar ekran çözünürlüğüne göre otomatik ayarlandı.\nAyarları Kaydet butonuna basmayı unutmayın.")
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Otomatik ayarlama başarısız: {e}")

    def reset_settings(self):
        reply = QMessageBox.question(self, 'Fabrika Ayarlarına Dön', 
                                     "Tüm ayarlarınız sıfırlanacak ve varsayılan değerlere dönecek.\nEmin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            config.reset_to_defaults()
            self.cfg = config.load_config()
            
            # UI'ı güncelle
            ocr = self.cfg.get("ocr_region", {})
            self.input_top.setText(str(ocr.get("top", 0)))
            self.input_left.setText(str(ocr.get("left", 0)))
            self.input_width.setText(str(ocr.get("width", 678)))
            self.input_height.setText(str(ocr.get("height", 635)))
            
            hk = self.cfg.get("hotkeys", {})
            self.input_hk_gallery.setText(hk.get("toggle_gallery", "f11"))
            self.input_hk_own.setText(hk.get("toggle_ownership", "f9"))
            
            QMessageBox.information(self, "Bilgi", "Ayarlar sıfırlandı.")

    def start_assistant(self, hide_launcher=True):
        # Eğer zaten yönetilen bir süreç varsa ve çalışıyorsa tekrar açma
        if self.assistant_process and self.assistant_process.poll() is None:
             return

        try:
            if getattr(sys, 'frozen', False):
                main_exe = os.path.join(APP_DIR, "main.exe")
                proc = subprocess.Popen([main_exe], cwd=APP_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                proc = subprocess.Popen([sys.executable, "main.py"], cwd=APP_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            
            # Kısa bir süre bekle ve hata kontrolü yap
            import time
            time.sleep(0.3)
            exit_code = proc.poll()
            
            if exit_code is not None:
                # Process crash oldu veya hemen kapandı
                stdout, stderr = proc.communicate(timeout=1)
                error_msg = stderr.decode('utf-8', errors='ignore') if stderr else ""
                
                if "OCR" in error_msg and "bulunamadı" in error_msg:
                    QMessageBox.critical(self, "OCR Hatası", 
                        "Hiçbir OCR motoru bulunamadı!\n\n"
                        "Çözüm 1: Windows OCR (Önerilen)\n"
                        "  • Ayarlar → Zaman ve Dil → Dil → İngilizce (US) ekle\n"
                        "  • Terminal: pip install winocr\n\n"
                        "Çözüm 2: Tesseract OCR\n"
                        "  • İndir: https://github.com/UB-Mannheim/tesseract/wiki\n"
                        "  • Kur: C:\\Program Files\\Tesseract-OCR\n"
                        "  • Terminal: pip install pytesseract")
                else:
                    QMessageBox.critical(self, "Hata", f"Asistan başlatılamadı (exit code: {exit_code})\n\n{error_msg[:500]}")
                return
            
            # Eğer Auto-Pilot aktifse süreci takip et (yönet)
            if self.autopilot_chk.isChecked():
                self.assistant_process = proc
            else:
                # Auto-Pilot kapalıysa asistan bağımsız çalışsın
                self.assistant_process = None
                
            if hide_launcher:
                self.close() # Launcher'ı kapat veya gizle
                # Eğer asistan başladıysa ve Launcher gizlendiyse, tray ikonunu da gizle (Birleştirilmiş İkon Hissi)
                if self.autopilot_chk.isChecked() and self.assistant_process:
                    self.tray_icon.hide()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Asistan başlatılamadı:\n{e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec_())
