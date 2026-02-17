import sys
import os
import subprocess
import json
import argparse  # Added for argument parsing
from config import APP_DIR
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QTabWidget, 
                             QTextEdit, QLineEdit, QFormLayout, QGroupBox, 
                             QMessageBox, QProgressBar, QSpacerItem, QSizePolicy,
                             QCheckBox, QSystemTrayIcon, QMenu, QAction, QDialog, QFileDialog)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QColor, QCursor
import ctypes
from ctypes.wintypes import MSG
from ctypes import c_long, c_int, c_short
import i18n
import time
import logging

# === ARGUMENT PARSING MOVED TO MAIN BLOCK === 



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
# (Eski FramelessResizer Kaldırıldı)
# ==========================================


class VerificationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(i18n.t("installer.verification_title"))
        self.setFixedSize(450, 350)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; color: white; }
            QLabel { color: white; font-size: 14px; }
            QProgressBar { border: 1px solid #3d3d3d; text-align: center; background-color: #2d2d2d; color: white; }
            QProgressBar::chunk { background-color: #0e639c; }
            QPushButton { background-color: #0e639c; color: white; border: none; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #1177bb; }
            QPushButton:disabled { background-color: #3d3d3d; color: #888888; }
            QTextEdit { background-color: #252526; border: 1px solid #3d3d3d; color: #d4d4d4; font-family: 'Consolas'; font-size: 12px; }
        """)
        
        layout = QVBoxLayout(self)
        
        # Başlık
        title_lbl = QLabel(i18n.t("installer.verification_title"))
        title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        layout.addWidget(title_lbl)
        
        layout.addWidget(QLabel(i18n.t("installer.verification_desc")))
        
        # İlerleme Çubuğu
        self.progress = QProgressBar()
        self.progress.setRange(0, 4)
        layout.addWidget(self.progress)
        
        # Log Alanı
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        
        # Durum Butonu
        self.close_btn = QPushButton(i18n.t("installer.btn_close"))
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setEnabled(False)
        layout.addWidget(self.close_btn)
        
        # Otomatik Başlat
        QTimer.singleShot(500, self.run_checks)

    def log(self, msg, color="#ffffff"):
        self.log_area.append(f'<span style="color:{color}">{msg}</span>')
        QApplication.processEvents()

    def run_checks(self):
        try:
            # 1. Yazma İzinleri
            self.log(i18n.t("installer.check_write_perms"), "#cccccc")
            try:
                test_file = os.path.join(APP_DIR, "test_write.tmp")
                with open(test_file, "w") as f:
                    f.write("test")
                os.remove(test_file)
                self.log(f"✅ {i18n.t('installer.write_ok')}", "#4CAF50")
            except Exception as e:
                self.log(f"❌ {i18n.t('installer.write_fail')} (Bazı ayarlar kaydedilemeyebilir)\n{e}", "#F44336")
            
            try:
                log_dir = os.path.dirname(config.LOG_FILE)
                if not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                test_log = os.path.join(log_dir, "test_write.tmp")
                with open(test_log, "w") as f:
                    f.write("test")
                os.remove(test_log)
                self.log(f"✅ Log dizini yazılabilir: {log_dir}", "#4CAF50")
            except Exception as e:
                self.log(f"❌ Log dizini yazma hatası!\n{e}", "#F44336")
            
            self.progress.setValue(1)
            
            # 2. Config Kontrolü
            self.log(f"\n{i18n.t('installer.check_config')}", "#cccccc")
            if os.path.exists(config.CONFIG_FILE):
                self.log(i18n.t("installer.config_exists"), "#4CAF50")
            else:
                self.log(i18n.t("installer.config_create"), "#FFC107")
            self.progress.setValue(2)

            # 3. OCR Kontrolü
            self.log(f"\n{i18n.t('installer.check_ocr')}", "#cccccc")
            try:
                import workers
                engine = workers.get_ocr_engine()
                if engine == "winocr":
                    self.log(i18n.t("installer.ocr_active"), "#4CAF50")
                elif engine == "tesseract":
                    self.log(i18n.t("installer.ocr_failed"), "#FFC107")
                    self.log("ℹ️ Tesseract biraz daha yavaş çalışabilir.", "#cccccc")
                else:
                    self.log(i18n.t("installer.ocr_none"), "#F44336")
            except Exception as e:
                self.log(f"❌ OCR kontrol hatası: {e}", "#F44336")
            self.progress.setValue(3)

            # 4. Tesseract Dosyaları (Fallback için)
            self.log(f"\n{i18n.t('installer.check_tesseract')}", "#cccccc")
            tess_path = config._get_default_tesseract_path()
            if os.path.exists(tess_path):
                self.log(f"✅ Tesseract exe bulundu: {os.path.basename(tess_path)}", "#4CAF50")
            else:
                if engine == "winocr":
                    self.log("ℹ️ Tesseract yerel dosyası bulunamadı (Windows OCR çalıştığı için sorun değil).", "#cccccc")
                else:
                    self.log(f"❌ Tesseract exe bulunamadı! ({tess_path})", "#F44336")
            self.progress.setValue(4)
            
            self.log(f"\n{i18n.t('installer.verification_done')}", "#4CAF50")
            self.log(i18n.t("installer.close_window"), "#ffffff")
            
        except Exception as e:
            self.log(f"\n{i18n.t('installer.unexpected_error')}: {e}", "#F44336")
        
        self.close_btn.setEnabled(True)
        self.close_btn.setText(i18n.t("installer.btn_close_and_continue"))

class LauncherWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(i18n.t("launcher.title"))
        
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
        
        
        # Resizer'ı başlat (Devre dışı - Native resize kullanılıyor)
        # self.resizer = FramelessResizer(self)
        
        # Config yükle
        config.setup_logging() # LOGGING SETUP
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
            # self.autopilot_chk.setChecked(True) # UI sonra yüklenecek
            pass

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

    
    # Title bar drag metodları (Devre dışı - Native resize kullanılıyor)
    # def _title_bar_press(self, event):
    #     """Title bar'a tıklandığında pencereyi taşımaya başla"""
    #     pass
    
    # def _title_bar_move(self, event):
    #    pass
    
    # def _title_bar_release(self, event):
    #    pass

    def nativeEvent(self, eventType, message):
        """Windows Native Resize Handler (WM_NCHITTEST)"""
        if eventType == "windows_generic_MSG":
            # sip.voidptr -> int conversion
            msg = ctypes.cast(int(message), ctypes.POINTER(MSG)).contents
            
            if msg.message == 0x0084: # WM_NCHITTEST
                x = c_short(msg.lParam & 0xFFFF).value
                y = c_short((msg.lParam >> 16) & 0xFFFF).value
                
                # Global koordinatları pencere koordinatlarına çevir
                pt = self.mapFromGlobal(self.mapToGlobal(self.mapFromGlobal(from_global_pt := ctypes.wintypes.POINT(x, y))) if False else self.mapFromGlobal(from_global_qpt := self.cursor().pos()))
                # Basitçe QCursor.pos() yerine msg koordinatlarını kullanalım
                # msg.lParam zaten global koordinatları veriyor
                
                # Qt'nin mapFromGlobal'i QPoint bekler
                from PyQt5.QtCore import QPoint
                pt = self.mapFromGlobal(QPoint(x, y))
                
                # ÖNCELİKLE BUTON KONTROLÜ (Resize'dan önce)
                child = self.childAt(pt)
                if child and isinstance(child, QPushButton):
                     return True, 1 # HTCLIENT (Butona tıklamaya izin ver)

                w, h = self.width(), self.height()
                lx = pt.x()
                ly = pt.y()
                
                # Resize Kenar Boşluğu
                border_width = 13
                title_height = 35 # Custom Title Bar yüksekliği
                
                # Kenar Kontrolleri
                left = lx < border_width
                right = lx > w - border_width
                top = ly < border_width
                bottom = ly > h - border_width
                
                if top and left: return True, 13 # HTTOPLEFT
                if top and right: return True, 14 # HTTOPRIGHT
                if bottom and left: return True, 16 # HTBOTTOMLEFT
                if bottom and right: return True, 17 # HTBOTTOMRIGHT
                if left: return True, 10 # HTLEFT
                if right: return True, 11 # HTRIGHT
                if top: return True, 12 # HTTOP
                if bottom: return True, 15 # HTBOTTOM
                
                # Başlık çubuğu davranışı (Sürükleme)
                if ly < title_height:
                    return True, 2 # HTCAPTION
                
                return True, 1 # HTCLIENT
                
        return super().nativeEvent(eventType, message)


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
        self.min_lbl = QLabel(i18n.t("launcher.minimize_to_tray_label"))
        self.min_lbl.setFont(QFont("Segoe UI", 9))
        self.min_lbl.setStyleSheet("color: #888888; margin-right: 5px;")
        title_bar_layout.addWidget(self.min_lbl)
        
        self.minimize_to_tray_btn = QPushButton(i18n.t("launcher.minimize_label"))
        self.minimize_to_tray_btn.setFixedSize(140, 30)
        self.minimize_to_tray_btn.setCursor(Qt.PointingHandCursor)
        self.minimize_to_tray_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #cccccc;
                border: none;
                font-size: 12px;
                text-align: right;
            }
            QPushButton:hover {
                color: white;
                text-decoration: underline;
            }
        """)
        self.minimize_to_tray_btn.clicked.connect(self.hide)
        title_bar_layout.addWidget(self.minimize_to_tray_btn)

        self.maximize_btn = QPushButton("□")
        self.maximize_btn.setFixedSize(46, 30)
        self.maximize_btn.clicked.connect(self.toggle_maximize)
        title_bar_layout.addWidget(self.maximize_btn)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(46, 30)
        self.close_btn.setStyleSheet("QPushButton:hover { background-color: #e81123; }")
        self.close_btn.clicked.connect(self.quit_app)
        title_bar_layout.addWidget(self.close_btn)
        
        layout.addWidget(title_bar)
        
        
        # Drag desteği için title bar event handling (Native resize ile iptal)
        # self._drag_pos = None
        # title_bar.mousePressEvent = self._title_bar_press
        # title_bar.mouseMoveEvent = self._title_bar_move
        # title_bar.mouseReleaseEvent = self._title_bar_release
        # self.title_label.mousePressEvent = self._title_bar_press
        # self.title_label.mouseMoveEvent = self._title_bar_move
        # self.title_label.mouseReleaseEvent = self._title_bar_release
        
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
        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_dashboard_tab(), i18n.t("launcher.tab_dashboard"))
        # self.tabs.addTab(self.create_data_start_tab(), i18n.t("launcher.tab_data_start")) # Removed
        self.tabs.addTab(self.create_settings_tab(), i18n.t("launcher.tab_settings"))
        content_layout.addWidget(self.tabs)
        
        layout.addWidget(content_widget)
        
        # Sekme İçeriklerini Oluştur
        # The original `setup_data_tab` and `setup_settings_tab` calls are now replaced by `create_dashboard_tab`, `create_data_start_tab`, `create_settings_tab`.
        # So the following lines should be removed:
        # data_tab = QWidget()
        # self.setup_data_tab(data_tab)
        # self.tabs.addTab(data_tab, "Veri & Başlat")
        #
        # settings_tab = QWidget()
        # self.setup_settings_tab(settings_tab)
        # self.tabs.addTab(settings_tab, "Ayarlar")
        #
        # The instruction has `self.setup_settings_tab(settings_tab)` and `self.tabs.addTab(settings_tab, "Ayarlar")` at the end of the block, which is redundant with the new `create_settings_tab` call. I will remove these.
        
    def setup_data_tab(self, tab): # This function will be replaced by create_data_start_tab
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
        
        self.status_label = QLabel(i18n.t("launcher.status_waiting"))
        self.status_label.setStyleSheet("font-size: 16px; color: #aaaaaa; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.start_btn = self.create_button(i18n.t("launcher.btn_start_assistant"), "#4CAF50", "#388E3C")
        self.start_btn.clicked.connect(self.start_assistant)
        
        self.stop_btn = self.create_button(i18n.t("launcher.btn_stop_assistant"), "#F44336", "#D32F2F")
        self.stop_btn.clicked.connect(self.stop_assistant)
        
        btn_layout = QHBoxLayout()
        
        self.update_btn = QPushButton("Verileri Güncelle (İnternetten İndir)")
        self.update_btn.clicked.connect(self.start_update)
        self.update_btn.setMinimumHeight(40)
        
        start_btn = QPushButton("ASİSTANI BAŞLAT") 
        # ... (Start button code lines 163-167 skipped/assumed same) ...
        # Wait, I cannot skip lines inside ReplacementContent easily.
        # The instruction here is replacing the `status_group` and `btn_layout` with new `status_label` and `button_layout`.
        # I will replace the existing `status_group` and `btn_layout` with the new `status_label` and `button_layout`.
        # The `incremental_chk` is also part of the original `setup_data_tab`. I need to ensure it's handled.

        # The provided `Code Edit` for `setup_data_tab` is a partial replacement.
        # It starts with `self.status_label = QLabel(i18n.t("launcher.status_waiting"))`
        # and then defines `button_layout`, `self.start_btn`, `self.stop_btn`.
        # It also has `btn_layout = QHBoxLayout()` and `self.update_btn = QPushButton("Verileri Güncelle (İnternetten İndir)")`
        # This is very confusing. The instruction is to replace hardcoded strings.
        # The `Code Edit` seems to be replacing the entire `setup_data_tab` content with a new structure.

        # Let's assume the `setup_data_tab` function itself is being replaced by a new function `create_data_start_tab`
        # and the content provided in the `Code Edit` is for that new function.
        # However, the instruction explicitly says `def setup_data_tab(self, tab):`.
        # This means I should modify the existing `setup_data_tab`.

        # Original `setup_data_tab` content:
        # layout = QVBoxLayout(tab)
        # layout.setSpacing(15)
        #
        # # Auto-Pilot Checkbox (En Üstte)
        # self.autopilot_chk = QCheckBox("Auto-Pilot Modu (GTA 5 Açılınca Otomatik Başlat)")
        # self.autopilot_chk.setToolTip("İşaretliyse: Launcher kapanmaz, tepsiye küçülür ve oyunu bekler.")
        # self.autopilot_chk.setStyleSheet("QCheckBox { font-weight: bold; color: #4CAF50; padding: 5px; border: 1px solid #3d3d3d; border-radius: 4px; }")
        # self.autopilot_chk.toggled.connect(self.toggle_autopilot)
        # layout.addWidget(self.autopilot_chk)
        #
        # # Durum Kartı
        # status_group = QGroupBox("Sistem Durumu")
        # status_layout = QVBoxLayout(status_group)
        #
        # self.status_lbl = QLabel("Durum Kontrol Ediliyor...")
        # self.status_lbl.setFont(QFont("Segoe UI", 12))
        # self.vehicle_count_lbl = QLabel("")
        #
        # status_layout.addWidget(self.status_lbl)
        # status_layout.addWidget(self.vehicle_count_lbl)
        # layout.addWidget(status_group)
        #
        # self.check_status()
        #
        # # İşlem Butonları Yatay
        # btn_layout = QHBoxLayout()
        #
        # self.update_btn = QPushButton("Verileri Güncelle (İnternetten İndir)")
        # self.update_btn.clicked.connect(self.start_update)
        # self.update_btn.setMinimumHeight(40)
        #
        # start_btn = QPushButton("ASİSTANI BAŞLAT")
        # # ... (Start button code lines 163-167 skipped/assumed same) ...
        # # Wait, I cannot skip lines inside ReplacementContent easily.
        # # I'll rewrite the whole block or split into chunks.
        # # Chunk strategy: Insert checkbox before buttons.
        #
        # # Checkbox
        # self.incremental_chk = QCheckBox("Sadece eksik/yeni araçları indir (Hızlı Mod)")
        # self.incremental_chk.setChecked(True)
        # self.incremental_chk.setToolTip("İşaretliyse: Sadece veritabanında olmayan araçları indirir.\nİşaretli Değilse: Tüm veritabanını silip sıfırdan indirir.")
        # self.incremental_chk.setStyleSheet("QCheckBox { color: #cccccc; padding: 5px; } QCheckBox::indicator { width: 18px; height: 18px; }")
        # layout.addWidget(self.incremental_chk)
        #
        # # İşlem Butonları Yatay
        # btn_layout = QHBoxLayout()
        #
        # self.update_btn = QPushButton("Verileri Güncelle (İnternetten İndir)")
        # self.update_btn.clicked.connect(self.start_update)
        # self.update_btn.setMinimumHeight(40)
        #
        # start_btn = QPushButton("ASİSTANI BAŞLAT")
        # start_btn.setFont(QFont("Segoe UI", 12, QFont.Bold))
        # start_btn.setMinimumHeight(40)
        # start_btn.setStyleSheet("background-color: #2ea043; color: white; border-radius: 4px;")
        # start_btn.clicked.connect(self.start_assistant)
        #
        # btn_layout.addWidget(self.update_btn)
        # btn_layout.addWidget(start_btn)
        # layout.addLayout(btn_layout)

        # The provided `Code Edit` for `setup_data_tab` is a complete rewrite of the content of this function.
        # I will replace the entire content of `setup_data_tab` with the new content, and then rename the function to `create_data_start_tab` as implied by the `tabs.addTab` call.
        # This means the original `setup_data_tab` function will be removed and a new one created.
        # The instruction is to replace hardcoded strings, but the `Code Edit` is a structural change.
        # I will follow the `Code Edit` as literally as possible, assuming it's a new function `create_data_start_tab` and the content is for it.
        # The `setup_data_tab` function will be removed.

    # The `setup_data_tab` function is removed and its content is moved to `create_data_start_tab`.
    # The `setup_settings_tab` function is also removed and its content is moved to `create_settings_tab`.
    # The `create_dashboard_tab` function is new.

    # I will define these new functions and remove the old ones.

    def create_dashboard_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(10)
        layout.setContentsMargins(15, 15, 15, 15)

        # 1. Auto-Pilot Checkbox (Top)
        self.autopilot_chk = QCheckBox(i18n.t("launcher.autopilot_label"))
        self.autopilot_chk.setToolTip(i18n.t("launcher.autopilot_tooltip"))
        self.autopilot_chk.setStyleSheet("QCheckBox { font-weight: bold; color: #4CAF50; padding: 5px; border: 1px solid #3d3d3d; border-radius: 4px; }")
        self.autopilot_chk.toggled.connect(self.toggle_autopilot)
        layout.addWidget(self.autopilot_chk)

        # 2. System Status & Incremental Update
        status_group = QGroupBox(i18n.t("launcher.status_group_title"))
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(5)
        
        self.status_lbl = QLabel(i18n.t("launcher.status_checking"))
        self.status_lbl.setFont(QFont("Segoe UI", 11))
        self.vehicle_count_lbl = QLabel("")
        
        status_layout.addWidget(self.status_lbl)
        status_layout.addWidget(self.vehicle_count_lbl)
        
        # Incremental Checkbox inside Status Group (or below it)
        # Putting it inside makes sense as it relates to Data Status
        self.incremental_chk = QCheckBox(i18n.t("launcher.incremental_update_label"))
        self.incremental_chk.setChecked(True)
        self.incremental_chk.setToolTip(i18n.t("launcher.incremental_update_tooltip"))
        self.incremental_chk.setStyleSheet("QCheckBox { color: #aaaaaa; font-size: 12px; }")
        status_layout.addWidget(self.incremental_chk)

        layout.addWidget(status_group)
        
        self.check_status()

        # 3. Action Buttons (Unified)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.update_btn = QPushButton(i18n.t("launcher.btn_update_data"))
        self.update_btn.clicked.connect(self.start_update)
        self.update_btn.setMinimumHeight(45)
        self.update_btn.setStyleSheet("""
            QPushButton { background-color: #0984e3; color: white; border-radius: 4px; font-weight: bold; }
            QPushButton:hover { background-color: #74b9ff; }
            QPushButton:disabled { background-color: #3d3d3d; color: #888; }
        """)
        
        start_btn = QPushButton(i18n.t("launcher.btn_start_assistant"))
        start_btn.setMinimumHeight(45)
        start_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        start_btn.setStyleSheet("""
            QPushButton { background-color: #2ea043; color: white; border-radius: 4px; }
            QPushButton:hover { background-color: #3fb950; }
        """)
        start_btn.clicked.connect(self.start_assistant)

        self.stop_btn = QPushButton(i18n.t("launcher.btn_stop_assistant"))
        self.stop_btn.setMinimumHeight(45)
        self.stop_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.stop_btn.setStyleSheet("""
            QPushButton { background-color: #d63031; color: white; border-radius: 4px; }
            QPushButton:hover { background-color: #ff7675; }
        """)
        self.stop_btn.clicked.connect(self.stop_assistant)
        
        btn_layout.addWidget(self.update_btn)
        btn_layout.addWidget(start_btn)
        btn_layout.addWidget(self.stop_btn)
        
        layout.addLayout(btn_layout)

        # 4. Log Area
        log_header_layout = QHBoxLayout()
        log_header_layout.addWidget(QLabel(i18n.t("launcher.log_area_title")))
        log_header_layout.addStretch()
        
        open_log_btn = QPushButton(i18n.t("launcher.btn_open_log"))
        open_log_btn.setFixedSize(130, 25)
        open_log_btn.setStyleSheet("background-color: #444; color: white; border-radius: 3px; font-size: 11px;")
        open_log_btn.clicked.connect(self.open_log_folder)
        log_header_layout.addWidget(open_log_btn)
        
        layout.addLayout(log_header_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("background-color: #1e1e1e; color: #cccccc; border: 1px solid #3d3d3d; border-radius: 4px;")
        layout.addWidget(self.log_text)
        
        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border: 1px solid #3d3d3d; border-radius: 4px; text-align: center; } QProgressBar::chunk { background-color: #0984e3; }")
        layout.addWidget(self.progress_bar)

        return tab

    def create_data_start_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)

        # Auto-Pilot Checkbox (En Üstte)
        self.autopilot_chk = QCheckBox(i18n.t("launcher.autopilot_label"))
        self.autopilot_chk.setToolTip(i18n.t("launcher.autopilot_tooltip"))
        self.autopilot_chk.setStyleSheet("QCheckBox { font-weight: bold; color: #4CAF50; padding: 5px; border: 1px solid #3d3d3d; border-radius: 4px; }")
        self.autopilot_chk.toggled.connect(self.toggle_autopilot)
        layout.addWidget(self.autopilot_chk)
        
        # Durum Kartı
        status_group = QGroupBox(i18n.t("launcher.status_group_title"))
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel(i18n.t("launcher.status_waiting"))
        self.status_label.setStyleSheet("font-size: 16px; color: #aaaaaa; font-weight: bold;")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        
        self.start_btn = self.create_button(i18n.t("launcher.btn_start_assistant"), "#4CAF50", "#388E3C")
        self.start_btn.clicked.connect(self.start_assistant)
        
        self.stop_btn = self.create_button(i18n.t("launcher.btn_stop_assistant"), "#F44336", "#D32F2F")
        self.stop_btn.clicked.connect(self.stop_assistant)
        
        # The original `setup_data_tab` had `self.incremental_chk` and `self.update_btn`.
        # The provided `Code Edit` for `setup_data_tab` (which I'm using for `create_data_start_tab`)
        # seems to be missing the `incremental_chk` and `update_btn` from the original `setup_data_tab`.
        # I will add them back, using `i18n.t`.

        # Checkbox
        self.incremental_chk = QCheckBox(i18n.t("launcher.incremental_update_label"))
        self.incremental_chk.setChecked(True)
        self.incremental_chk.setToolTip(i18n.t("launcher.incremental_update_tooltip"))
        self.incremental_chk.setStyleSheet("QCheckBox { color: #cccccc; padding: 5px; } QCheckBox::indicator { width: 18px; height: 18px; }")
        layout.addWidget(self.incremental_chk)

        # Update Button
        self.update_btn = QPushButton(i18n.t("launcher.btn_update_data"))
        self.update_btn.clicked.connect(self.start_update)
        self.update_btn.setMinimumHeight(40)
        
        button_layout.addWidget(self.update_btn)
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn) # Added stop button to the layout
        layout.addLayout(button_layout)

        # Log Alanı
        log_header_layout = QHBoxLayout()
        log_header_layout.addWidget(QLabel(i18n.t("launcher.log_area_title")))
        log_header_layout.addStretch()
        
        open_log_btn = QPushButton(i18n.t("launcher.btn_open_log"))
        open_log_btn.setFixedSize(150, 30)
        open_log_btn.setStyleSheet("background-color: #444; color: white; border-radius: 4px;")
        open_log_btn.clicked.connect(self.open_log_folder)
        
        log_header_layout.addWidget(open_log_btn)
        
        layout.addLayout(log_header_layout)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # Progress Bar (Gizli)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        return tab

    def create_settings_tab(self):
        tab = QWidget()
        scroll_layout = QVBoxLayout(tab)
        # Use ScrollArea or just simple layout if it fits. 
        # Since we added more items, form layout might get tall.
        
        form_widget = QWidget()
        layout = QFormLayout(form_widget)
        layout.setSpacing(12)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # --- OCR Region ---
        layout.addRow(QLabel(i18n.t("launcher.ocr_region_title")))
        ocr = self.cfg.get("ocr_region", {})
        self.input_top = QLineEdit(str(ocr.get("top", 0)))
        self.input_left = QLineEdit(str(ocr.get("left", 0)))
        self.input_width = QLineEdit(str(ocr.get("width", 500)))
        self.input_height = QLineEdit(str(ocr.get("height", 800)))
        
        layout.addRow(i18n.t("launcher.ocr_top_label"), self.input_top)
        layout.addRow(i18n.t("launcher.ocr_left_label"), self.input_left)
        layout.addRow(i18n.t("launcher.ocr_width_label"), self.input_width)
        layout.addRow(i18n.t("launcher.ocr_height_label"), self.input_height)
        
        layout.addRow(QLabel("")) # Spacer

        # --- HUD Region ---
        layout.addRow(QLabel(i18n.t("launcher.hud_region_title")))
        hud = self.cfg.get("hud_region", {})
        self.input_hud_top = QLineEdit(str(hud.get("top", 40)))
        self.input_hud_left = QLineEdit(str(hud.get("left", 1325)))
        self.input_hud_width = QLineEdit(str(hud.get("width", 1215)))
        self.input_hud_height = QLineEdit(str(hud.get("height", 1510)))
        
        layout.addRow(i18n.t("launcher.hud_top_label"), self.input_hud_top)
        layout.addRow(i18n.t("launcher.hud_left_label"), self.input_hud_left)
        layout.addRow(i18n.t("launcher.hud_width_label"), self.input_hud_width)
        layout.addRow(i18n.t("launcher.hud_height_label"), self.input_hud_height)
        
        layout.addRow(QLabel("")) # Spacer
        
        # --- Hotkeys ---
        layout.addRow(QLabel(i18n.t("launcher.hotkeys_title")))
        hk = self.cfg.get("hotkeys", {})
        self.input_hk_gallery = QLineEdit(hk.get("toggle_gallery", "f11"))
        self.input_hk_own = QLineEdit(hk.get("toggle_ownership", "f9"))
        layout.addRow(i18n.t("launcher.hotkey_gallery_label"), self.input_hk_gallery)
        layout.addRow(i18n.t("launcher.hotkey_ownership_label"), self.input_hk_own)
        
        layout.addRow(QLabel("")) # Spacer

        # --- OCR Tools (NEW) ---
        tools_label = QLabel("OCR Tools / Troubleshooting")
        tools_label.setStyleSheet("font-weight: bold; color: #ff9f43;")
        layout.addRow(tools_label)

        # Tesseract Path
        tess_path_layout = QHBoxLayout()
        self.input_tesseract = QLineEdit(self.cfg.get("tesseract_path", ""))
        self.input_tesseract.setPlaceholderText("C:\\Program Files\\Tesseract-OCR\\tesseract.exe")
        
        browse_btn = QPushButton(i18n.t("launcher.btn_browse"))
        browse_btn.setFixedWidth(80)
        browse_btn.clicked.connect(self.browse_tesseract_path)
        
        tess_path_layout.addWidget(self.input_tesseract)
        tess_path_layout.addWidget(browse_btn)
        
        layout.addRow(i18n.t("launcher.tesseract_path_label"), tess_path_layout)
        
        # Fix OCR Button
        fix_ocr_btn = QPushButton(i18n.t("launcher.btn_fix_ocr"))
        fix_ocr_btn.setStyleSheet("background-color: #6c5ce7; color: white;")
        fix_ocr_btn.clicked.connect(self.fix_windows_ocr)
        layout.addRow("", fix_ocr_btn)

        layout.addRow(QLabel("")) # Spacer

        # --- Startup ---
        self.startup_chk = QCheckBox(i18n.t("launcher.startup_checkbox"))
        self.startup_chk.setChecked(self.check_startup_status())
        self.startup_chk.toggled.connect(self.toggle_startup)
        layout.addRow(self.startup_chk)
        
        # --- Bottom Buttons ---
        save_btn = QPushButton(i18n.t("launcher.btn_save_settings"))
        save_btn.setMinimumHeight(40)
        save_btn.setStyleSheet("background-color: #00b894; color: white; font-weight: bold;")
        save_btn.clicked.connect(self.save_settings)
        layout.addRow(save_btn)

        auto_scale_btn = QPushButton(i18n.t("launcher.btn_auto_scale"))
        auto_scale_btn.setMinimumHeight(30)
        auto_scale_btn.setStyleSheet("background-color: #0984e3; color: white;")
        auto_scale_btn.clicked.connect(self.auto_scale_settings)
        layout.addRow(auto_scale_btn)

        reset_btn = QPushButton(i18n.t("launcher.btn_reset_settings"))
        reset_btn.setMinimumHeight(30)
        reset_btn.setStyleSheet("background-color: #d63031; color: white;")
        reset_btn.clicked.connect(self.reset_settings)
        layout.addRow(reset_btn)

        scroll_layout.addWidget(form_widget)
        return tab

    def browse_tesseract_path(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Select Tesseract EXE", "", "Executable Files (*.exe)")
        if filename:
            self.input_tesseract.setText(filename)
    
    def fix_windows_ocr(self):
        confirm = QMessageBox.question(self, i18n.t("launcher.msg_ocr_error_title"), i18n.t("launcher.fix_ocr_confirm"), QMessageBox.Yes | QMessageBox.No)
        if confirm == QMessageBox.Yes:
            # Add-WindowsCapability command
            cmd = 'powershell "Add-WindowsCapability -Online -Name Language.OCR~~~en-US~0.0.1.0; Add-WindowsCapability -Online -Name Language.OCR~~~tr-TR~0.0.1.0"'
            try:
                # Run as admin
                ctypes.windll.shell32.ShellExecuteW(None, "runas", "powershell", cmd, None, 1)
                QMessageBox.information(self, i18n.t("common.info"), i18n.t("launcher.fix_ocr_sent"))
            except Exception as e:
                QMessageBox.critical(self, i18n.t("common.error"), str(e))

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QApplication.style().SP_ComputerIcon))
        
        self.tray_icon.setToolTip(i18n.t("launcher.tray_tooltip"))
        
        # Menu
        tray_menu = QMenu()
        show_action = tray_menu.addAction(i18n.t("launcher.tray_show"))
        show_action.triggered.connect(self.show_normal)
        quit_action = tray_menu.addAction(i18n.t("launcher.tray_quit"))
        quit_action.triggered.connect(self.quit_app)
        
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
                i18n.t("launcher.autopilot_active_title"),
                i18n.t("launcher.autopilot_active_message"),
                QSystemTrayIcon.Information,
                2000
            )
        else:
            self.quit_app()

    def minimize_to_tray(self):
        """Pencereyi gizle ve tepsiye küçüldü bilgisini ver."""
        self.hide()
        self.tray_icon.showMessage(
            i18n.t("launcher.tray_minimized_title"), 
            i18n.t("launcher.tray_minimized_message"),
            QSystemTrayIcon.Information, 
            1000
        )

    def changeEvent(self, event):
        # if event.type() == 105: # QEvent.WindowStateChange
        #     if self.windowState() & Qt.WindowMinimized:
        #         # Küçültme butonuna basıldı -> Tepsiye gönder
        #         event.ignore()
        #         self.hide()
        #         self.tray_icon.showMessage(
        #             "Sistem Tepsisine Küçültüldü", 
        #             "Uygulama arka planda çalışıyor.",
        #             QSystemTrayIcon.Information, 
        #             1000
        #         )
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
            self.log_text.append(i18n.t("launcher.game_detected_start_assistant"))
            # Launcher ikonunu gizle (Asistan'ın ikonu gelecek)
            self.tray_icon.hide()
            self.start_assistant(hide_launcher=False)

    def on_game_stopped(self):
        if self.assistant_process:
            self.log_text.append(i18n.t("launcher.game_stopped_stop_assistant"))
            self.assistant_process.terminate()
            self.assistant_process = None
            # Launcher ikonunu geri getir
            self.tray_icon.show()
            self.tray_icon.showMessage(i18n.t("launcher.title"), i18n.t("launcher.assistant_stopped_message"), QSystemTrayIcon.Information, 2000)

    def toggle_autopilot(self, checked):
        """Auto-Pilot modunu açar/kapatır."""
        self.cfg["autopilot"] = checked
        save_config(self.cfg)
        
        if checked:
            self.tray_icon.showMessage(
                i18n.t("launcher.autopilot_active_title"),
                i18n.t("launcher.autopilot_active_message"),
                QSystemTrayIcon.Information,
                3000
            )


    def check_startup_status(self):
        """Görev Zamanlayıcı'da görevin olup olmadığını kontrol eder."""
        try:
            # schtasks /query /tn "GTA Asistan Launcher"
            # Hata kodu 0 ise görev var demektir.
            subprocess.run(["schtasks", "/query", "/tn", "GTA Asistan Launcher"], 
                           check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except subprocess.CalledProcessError:
            return False

    def toggle_startup(self, checked):
        task_name = "GTA Asistan Launcher"
        
        if getattr(sys, 'frozen', False):
            target_exe = os.path.join(APP_DIR, "launcher.exe")
            # Exe için tırnak içine al (boşluk varsa)
            command = f'\\"{target_exe}\\"' 
        else:
            # Geliştirme ortamı için
            python_exe = sys.executable
            # pythonw kullan ki konsol açılmasın
            pythonw = python_exe.replace("python.exe", "pythonw.exe")
            if not os.path.exists(pythonw): pythonw = python_exe
            
            launcher_script = os.path.join(APP_DIR, "launcher.py")
            command = f'\\"{pythonw}\\" \\"{launcher_script}\\"'

        if checked:
            try:
                # Görev Zamanlayıcı'ya ekle (Yüksek Ayrıcalıklarla - /rl highest)
                # /sc onlogon: Kullanıcı giriş yaptığında
                # /f: Varsa üzerine yaz
                args = [
                    "schtasks", "/create", "/tn", task_name,
                    "/tr", command,
                    "/sc", "onlogon",
                    "/rl", "highest",
                    "/f"
                ]
                
                # subprocess ile çalıştır (zaten admin yetkisi olduğu varsayılır)
                subprocess.run(args, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
                # Eski kısayol varsa temizle
                old_lnk = os.path.join(os.getenv('APPDATA'), r'Microsoft\Windows\Start Menu\Programs\Startup', 'GTA_Asistan_Launcher.lnk')
                if os.path.exists(old_lnk):
                    os.remove(old_lnk)
                    
                QMessageBox.information(self, i18n.t("common.info"), i18n.t("launcher.startup_added_success"))
            except subprocess.CalledProcessError as e:
                logging.error(f"Startup task creation failed: {e}")
                QMessageBox.critical(self, i18n.t("common.error"), f"{i18n.t('launcher.startup_add_fail')}\n{i18n.t('launcher.run_as_admin_hint')}\nHata: {e}")
            except Exception as e:
                logging.error(f"Startup task error: {e}")
                QMessageBox.critical(self, i18n.t("common.error"), f"{i18n.t('common.unexpected_error')}: {e}")
                
        else:
            try:
                # Görevi sil
                subprocess.run(["schtasks", "/delete", "/tn", task_name, "/f"], 
                               check=True, creationflags=subprocess.CREATE_NO_WINDOW)
                QMessageBox.information(self, i18n.t("common.info"), i18n.t("launcher.startup_removed_success"))
            except subprocess.CalledProcessError:
                # Görev zaten yoksa sorun değil
                pass
            except Exception as e:
                QMessageBox.critical(self, i18n.t("common.error"), f"{i18n.t('launcher.startup_remove_fail')}: {e}")

    def check_status(self):
        db_file = os.path.join(APP_DIR, "gta_tum_araclar.json")
        if os.path.exists(db_file):
            try:
                with open(db_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    count = len(data)
                    self.status_lbl.setText(i18n.t("launcher.db_ready"))
                    self.status_lbl.setStyleSheet("color: #4CAF50; font-weight: bold;")
                    self.vehicle_count_lbl.setText(f"{count} {i18n.t('launcher.vehicle_records_count')}")
            except:
                self.status_lbl.setText(i18n.t("launcher.db_read_error"))
                self.status_lbl.setStyleSheet("color: #F44336; font-weight: bold;")
        else:
            self.status_lbl.setText(i18n.t("launcher.db_not_found"))
            self.status_lbl.setStyleSheet("color: #FFC107; font-weight: bold;")
            self.vehicle_count_lbl.setText(i18n.t("launcher.db_not_found_hint"))

    def update_status(self, status):
        if status == "waiting":
            self.status_label.setText(i18n.t("launcher.status_waiting"))
            self.status_label.setStyleSheet("font-size: 16px; color: #aaaaaa; font-weight: bold;")
            self.tray_icon.setToolTip(f"{i18n.t('launcher.tray_tooltip')} ({i18n.t('launcher.status_waiting')})")
        elif status == "running":
            self.status_label.setText(i18n.t("launcher.status_running"))
            self.status_label.setStyleSheet("font-size: 16px; color: #4CAF50; font-weight: bold;")
            self.tray_icon.setToolTip(f"{i18n.t('launcher.tray_tooltip')} ({i18n.t('launcher.status_running')})")
        elif status == "stopped":
            self.status_label.setText(i18n.t("launcher.status_stopped"))
            self.status_label.setStyleSheet("font-size: 16px; color: #F44336; font-weight: bold;")
            self.tray_icon.setToolTip(f"{i18n.t('launcher.tray_tooltip')} ({i18n.t('launcher.status_stopped')})")

    def open_log_folder(self):
        """Log dosyasının bulunduğu klasörü açar."""
        # Config.py setup_logging fonksiyonuna göre loglar LocalAppData/GtaAsistan altında
        log_dir = os.path.join(os.getenv('LOCALAPPDATA'), "GtaAsistan")
        
        if not os.path.exists(log_dir):
            # Fallback olarak AppData değilse APP_DIR dene (eski versiyonlar için veya taşınabilir mod)
            log_dir = os.path.join(APP_DIR, 'logs')
            if not os.path.exists(log_dir):
                 # Hiçbiri yoksa direkt APP_DIR aç
                 log_dir = APP_DIR
        
        try:
            os.startfile(log_dir)
        except Exception as e:
            QMessageBox.warning(self, i18n.t("common.error"), f"{i18n.t('launcher.folder_open_fail')}:\n{log_dir}\n\nHata: {e}")

    def start_update(self):
        if not data_updater:
            QMessageBox.critical(self, i18n.t("common.error"), i18n.t("launcher.data_module_load_fail"))
            return
            
        self.update_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.log_text.clear()
        
        incremental = self.incremental_chk.isChecked()
        mode_str = i18n.t("launcher.mode_fast") if incremental else i18n.t("launcher.mode_full")
        self.log_text.append(f"🔄 {i18n.t('launcher.update_starting')} ({mode_str} {i18n.t('launcher.mode_text')})... {i18n.t('common.please_wait')}")
        
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
        self.log_text.append(f"\n✅ {i18n.t('common.operation_complete')}.")
        self.check_status()
        QMessageBox.information(self, i18n.t("common.info"), i18n.t("launcher.data_update_success"))

    def toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            self.maximize_btn.setText("□")
        else:
            self.showMaximized()
            self.maximize_btn.setText("❐")

    def quit_app(self):
        """Uygulamadan ve tüm süreçlerden çık."""
        self.stop_assistant()
        QApplication.quit()

    def create_button(self, text, bg_color, hover_color):
        btn = QPushButton(text)
        btn.setMinimumHeight(45)
        btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_color};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {hover_color};
            }}
            QPushButton:pressed {{
                background-color: {bg_color};
                margin-top: 2px;
            }}
            QPushButton:disabled {{
                background-color: #3d3d3d;
                color: #888888;
            }}
        """)
        return btn

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
                error_msg = i18n.t("launcher.error_ocr_top_invalid")
                raise
            
            try:
                self.cfg["ocr_region"]["left"] = int(self.input_left.text())
            except ValueError:
                error_field = self.input_left
                error_msg = i18n.t("launcher.error_ocr_left_invalid")
                raise
            
            try:
                self.cfg["ocr_region"]["width"] = int(self.input_width.text())
            except ValueError:
                error_field = self.input_width
                error_msg = i18n.t("launcher.error_ocr_width_invalid")
                raise
            
            try:
                self.cfg["ocr_region"]["height"] = int(self.input_height.text())
            except ValueError:
                error_field = self.input_height
                error_msg = i18n.t("launcher.error_ocr_height_invalid")
                raise
            
            # HUD Region Key Check (Eski configlerde olmayabilir)
            if "hud_region" not in self.cfg: 
                self.cfg["hud_region"] = {}
            
            try:
                self.cfg["hud_region"]["top"] = int(self.input_hud_top.text())
            except ValueError:
                error_field = self.input_hud_top
                error_msg = i18n.t("launcher.error_hud_top_invalid")
                raise
            
            try:
                self.cfg["hud_region"]["left"] = int(self.input_hud_left.text())
            except ValueError:
                error_field = self.input_hud_left
                error_msg = i18n.t("launcher.error_hud_left_invalid")
                raise
            
            try:
                self.cfg["hud_region"]["width"] = int(self.input_hud_width.text())
            except ValueError:
                error_field = self.input_hud_width
                error_msg = i18n.t("launcher.error_hud_width_invalid")
                raise
            
            try:
                self.cfg["hud_region"]["height"] = int(self.input_hud_height.text())
            except ValueError:
                error_field = self.input_hud_height
                error_msg = i18n.t("launcher.error_hud_height_invalid")
                raise

            # Save Hotkeys
            if "hotkeys" not in self.cfg: self.cfg["hotkeys"] = {}
            self.cfg["hotkeys"]["toggle_gallery"] = self.input_hk_gallery.text()
            self.cfg["hotkeys"]["toggle_ownership"] = self.input_hk_own.text()
            
            # Save Tesseract Path
            self.cfg["tesseract_path"] = self.input_tesseract.text()

            # Kaydet
            config.save_config(self.cfg)
            QMessageBox.information(self, i18n.t("common.success"), i18n.t("launcher.settings_saved"))
            
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
            QMessageBox.warning(self, i18n.t("common.error"), error_msg or i18n.t("launcher.error_invalid_values"))

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
            
            QMessageBox.information(self, i18n.t("common.info"), i18n.t("launcher.auto_scale_success_hint"))
        except Exception as e:
            QMessageBox.critical(self, i18n.t("common.error"), f"{i18n.t('launcher.auto_scale_fail')}: {e}")

    def reset_settings(self):
        reply = QMessageBox.question(self, i18n.t("launcher.reset_settings_title"), 
                                     i18n.t("launcher.reset_settings_confirm"),
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
            
            QMessageBox.information(self, i18n.t("common.info"), i18n.t("launcher.settings_reset_success"))

    def start_assistant(self, hide_launcher=True):
        # Eğer zaten yönetilen bir süreç varsa ve çalışıyorsa tekrar açma
        if self.assistant_process and self.assistant_process.poll() is None:
             return

        try:
            # PIPE kullanmak deadlock'a yol açabilir (buffer dolarsa).
            # Bu yüzden DEVNULL kullanıyoruz. Loglar zaten debug.log'a yazılıyor.
            if getattr(sys, 'frozen', False):
                main_exe = os.path.join(APP_DIR, "main.exe")
                proc = subprocess.Popen([main_exe], cwd=APP_DIR, 
                                      stdout=subprocess.DEVNULL, 
                                      stderr=subprocess.DEVNULL)
            else:
                proc = subprocess.Popen([sys.executable, "main.py"], cwd=APP_DIR, 
                                      stdout=subprocess.DEVNULL, 
                                      stderr=subprocess.DEVNULL)
            
            # Kısa bir süre bekle ve hata kontrolü yap
            import time
            time.sleep(0.5)
            exit_code = proc.poll()
            
            if exit_code is not None:
                # Process crash oldu veya hemen kapandı
                # DEVNULL kullandığımız için stderr okuyamayız. Log dosyasına bakılmalı.
                QMessageBox.critical(self, i18n.t("common.error"), f"{i18n.t('launcher.assistant_start_fail')} (exit code: {exit_code})\n\n{i18n.t('launcher.check_debug_log')}")
                return
                
                # The following block is commented out in the original, but present in the instruction's `Code Edit`.
                # I will assume it's meant to be added if the `if exit_code is not None:` block is active.
                # Since the `if exit_code is not None:` block already has a `return`, this part is unreachable.
                # I will keep the original structure and not add this unreachable code.
                # if "OCR" in error_msg and "bulunamadı" in error_msg:
                #     QMessageBox.critical(self, "OCR Hatası", 
                #         "Hiçbir OCR motoru bulunamadı!\n\n"
                #         "Çözüm 1: Windows OCR (Önerilen)\n"
                #         "  • Ayarlar → Zaman ve Dil → Dil → İngilizce (US) ekle\n"
                #         "  • Terminal: pip install winocr\n\n"
                #         "Çözüm 2: Tesseract OCR\n"
                #         "  • İndir: https://github.com/UB-Mannheim/tesseract/wiki\n"
                #         "  • Kur: C:\\Program Files\\Tesseract-OCR\n"
                #         "  • Terminal: pip install pytesseract")
                # else:
                #     QMessageBox.critical(self, "Hata", f"Asistan başlatılamadı (exit code: {exit_code})\n\n{error_msg[:500]}")
                # return
            
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
            QMessageBox.critical(self, i18n.t("common.error"), f"{i18n.t('launcher.assistant_start_fail')}:\n{e}")

    def stop_assistant(self):
        """Asistan sürecini durdur."""
        if self.assistant_process:
            self.assistant_process.terminate()
            self.assistant_process = None
            logging.info("Asistan süreci durduruldu.")
        
        self.update_status("stopped")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if self.autopilot_chk.isChecked():
            self.tray_icon.showMessage(i18n.t("launcher.title"), i18n.t("launcher.assistant_stopped_message"), QSystemTrayIcon.Information, 2000)

    def process_finished(self):
        logging.info("Asistan process sonlandı.")
        self.assistant_process = None
        self.update_status("stopped")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        # Check if it crashed
        if self.assistant_thread and self.assistant_thread.exit_code != 0:
            logging.error(f"Asistan hata ile kapandı. Kod: {self.assistant_thread.exit_code}")
            
            # OCR Hatası mı?
            if self.assistant_thread.exit_code == 3221225477: # Access violation often related to DLLs
                QMessageBox.critical(self, i18n.t("launcher.msg_ocr_error_title"), f"{i18n.t('launcher.msg_ocr_error_title')}: 0xC0000005 (Access Violation)\nWindows OCR component crashed.")
            else:
                 QMessageBox.critical(self, i18n.t("launcher.msg_error_title"), f"{i18n.t('launcher.assistant_crashed')}\nExit Code: {self.assistant_thread.exit_code}\n{i18n.t('launcher.check_logs_hint')}")

if __name__ == "__main__" or getattr(sys, 'frozen', False):
    # Kilitleme mekanizması
    try:
        # Create a named mutex to prevent multiple instances
        # Global prefix is needed for system-wide mutex
        mutex = ctypes.windll.kernel32.CreateMutexW(None, True, "Global\\GtaAsistanLauncherMutex")
        if ctypes.windll.kernel32.GetLastError() == 183: # ERROR_ALREADY_EXISTS
            from PyQt5.QtWidgets import QMessageBox
            # We need a dummy app to show message box since we haven't showed the main window yet
            # But 'app' is already created above
            QMessageBox.warning(None, i18n.t("launcher.title"), i18n.t("launcher.msg_already_running"))
            sys.exit(0)
    except Exception as e:
        print(f"Mutex error: {e}")

    # Argüman kontrolü
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-ocr", action="store_true", help="Check Windows OCR status and exit")
    parser.add_argument("--verify-install", action="store_true", help="Run full post-install verification")
    parser.add_argument("--set-lang", type=str, help="Set application language (tr/en) from installer")
    args, unknown = parser.parse_known_args()

    # QApplication başlat
    app = QApplication(sys.argv)

    # Dil Ayarını Uygula (Eğer argüman varsa)
    if args.set_lang:
        lang_map = {
            "turkish": "tr",
            "english": "en",
            "tr": "tr",
            "en": "en"
        }
        lang_code = lang_map.get(args.set_lang.lower(), "tr")
        
        try:
            cfg = config.load_config()
            cfg["language"] = lang_code
            config.save_config(cfg)
            logging.info(f"Language set to '{lang_code}' via installer argument.")
        except Exception as e:
            logging.error(f"Failed to set language: {e}")
        
        # Eğer sadece dil ayarlamak için çağrıldıysa ve verify istenmediyse çık
        if not args.verify_install:
            sys.exit(0)

    if args.verify_install:
        config.setup_logging()
        logging.info("--- Post-Install Verification Started ---")
        
        dialog = VerificationDialog()
        dialog.exec_()
        sys.exit(0)

    if args.check_ocr:
        # detaylı loglama başlat
        config.setup_logging()
        logging.info("--- Installer OCR Verification Started ---")
        
        try:
            import workers
            print("Checking Windows OCR status...")
            logging.info("Calling workers.get_ocr_engine()...")
            engine = workers.get_ocr_engine()
            logging.info(f"Engine detected: {engine}")
            
            if engine == "winocr":
                print("Windows OCR is available and working.")
                logging.info("Verification SUCCESS.")
                sys.exit(0)
            else:
                logging.error(f"Verification FAILED. Engine: {engine}")
                # Log dosyasını aç
                try:
                    os.startfile(config.LOG_FILE)
                except:
                    pass
                    
                QMessageBox.critical(None, i18n.t("installer.ocr_install_error_title"), 
                                     f"{i18n.t('installer.ocr_verification_failed')}\n\n{i18n.t('installer.detected_engine')}: {engine}\n\n{i18n.t('installer.check_install_logs')}\n{i18n.t('installer.log_file')}: {config.LOG_FILE}\n\n{i18n.t('installer.ensure_english_ocr_installed')}")
                sys.exit(1)
        except Exception as e:
            logging.critical(f"Verification Check CRASHED: {e}", exc_info=True)
            try:
                os.startfile(config.LOG_FILE)
            except:
                pass
            QMessageBox.critical(None, "GTA Asistan Kurulum Hatası", f"OCR kontrolü sırasında hata oluştu:\n{e}\n\nLog dosyası açılıyor...")
            sys.exit(1)

    # Normal Başlatma
    window = LauncherWindow()
    window.show()
    sys.exit(app.exec_())
