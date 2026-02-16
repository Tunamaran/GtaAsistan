# === UI Modülü ===
# PyQt5 - Widgets
from PyQt5.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QGridLayout, QFrame,
    QHBoxLayout, QLineEdit, QComboBox, QPushButton,
    QScrollArea, QStackedWidget, QCheckBox, QApplication,
    QFormLayout, QSpinBox, QFileDialog, QMessageBox,
    QRubberBand, QLayout, QSizePolicy, QGroupBox, QMenu, QAction
)
# PyQt5 - Core
from PyQt5.QtCore import (
    Qt, QTimer, QRect, QSize, QPoint, QRectF, pyqtSignal, QEvent
)
# PyQt5 - GUI
from PyQt5.QtGui import (
    QFont, QFontMetrics, QPainter, QPainterPath, QColor, QPen, QBrush,
    QPixmap, QImage, QCursor, QLinearGradient
)

# Proje Modülleri
from config import load_config, save_config
from database import get_smart_badges, get_vehicle_advice, parse_number, load_garage, get_garage_stats, toggle_vehicle_ownership
from workers import ImageLoaderThread

# ==========================================
# THEME & DESIGN SYSTEM
# ==========================================
class Theme:
    """Uygulama renk paleti ve stil sabitleri"""
    # Renkler
    PRIMARY = "#00FF96"
    PRIMARY_DARK = "#00b894"
    BACKGROUND = "#121212"
    SURFACE = "#2d3436"
    SURFACE_LIGHT = "#3d4d56"
    ERROR = "#d63031"
    ERROR_LIGHT = "#ff7675"
    WARNING = "#fdcb6e"
    SUCCESS = "#00b894"
    
    # Metin Renkleri (WCAG AA uyumlu)
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#B2BEC3"  # 8.5:1 contrast
    TEXT_DISABLED = "#7F8C8D"   # 4.1:1 contrast
    TEXT_HINT = "#636e72"
    
    # Border & Shadow
    BORDER_COLOR = "#444444"
    BORDER_HOVER = "#00FF96"
    SHADOW = "rgba(0, 0, 0, 0.3)"
    
    # Border Radius
    RADIUS_SMALL = 4
    RADIUS_MEDIUM = 6
    RADIUS_LARGE = 12
    
    # Opacity
    OPACITY_DISABLED = 0.5
    OPACITY_HOVER = 0.8

class Layout:
    """Layout boyut sabitleri"""
    # Card boyutları
    CARD_WIDTH = 290
    CARD_HEIGHT = 320
    CARD_IMAGE_WIDTH = 260
    CARD_IMAGE_HEIGHT = 145
    
    # Spacing
    SPACING_TINY = 5
    SPACING_SMALL = 10
    SPACING_MEDIUM = 15
    SPACING_LARGE = 25
    SPACING_XLARGE = 40
    
    # Margins
    MARGIN_WINDOW = 10
    MARGIN_CONTENT = 25
    
    # HUD
    HUD_MIN_WIDTH = 220
    HUD_MAX_HEIGHT = 32
    
    # Button
    BUTTON_HEIGHT = 40
    BUTTON_MIN_WIDTH = 120

class Typography:
    """Tipografi sistemi"""
    # Font Aileleri
    FONT_FAMILY = "Segoe UI"
    
    # Font Boyutları (pt)
    SIZE_HUGE = 24
    SIZE_XLARGE = 18
    SIZE_LARGE = 16
    SIZE_TITLE = 14
    SIZE_BODY = 11
    SIZE_SMALL = 10
    SIZE_TINY = 9
    SIZE_CAPTION = 8
    
    # Font Ağırlıkları
    WEIGHT_NORMAL = QFont.Normal
    WEIGHT_BOLD = QFont.Bold
    
    @staticmethod
    def get(size, weight=QFont.Normal):
        """Font nesnesi döndür"""
        return QFont(Typography.FONT_FAMILY, size, weight)



# ==========================================
# FLOW LAYOUT (Etiketlerin sığması için)
# ==========================================
class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super(FlowLayout, self).__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.contentsMargins().top(), 2 * self.contentsMargins().top())
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0
        spacing = self.spacing()

        for item in self.itemList:
            wid = item.widget()
            spaceX = spacing + wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            spaceY = spacing + wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()

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
        rect = self.window.geometry()
        m_pos = global_pos
        
        if "L" in self._resize_dir: rect.setLeft(m_pos.x())
        if "R" in self._resize_dir: rect.setRight(m_pos.x())
        if "T" in self._resize_dir: rect.setTop(m_pos.y())
        if "B" in self._resize_dir: rect.setBottom(m_pos.y())
        
        if rect.width() > 400 and rect.height() > 300:
            self.window.setGeometry(rect)

# ==========================================
# 1. KART TASARIMI (SENİN KODUN - DOKUNULMADI)
# ==========================================

class VehicleCard(QFrame):

    clicked = pyqtSignal(dict)

    

    def __init__(self, vehicle_data):

        super().__init__()

        self.vehicle_data = vehicle_data

        self.setFixedSize(290, 320)

        self.setAttribute(Qt.WA_StyledBackground, True)

        self.setStyleSheet("""

            VehicleCard { background-color: rgba(30, 30, 30, 180); border-radius: 12px; border: 2px solid #333; }

            VehicleCard:hover { background-color: rgba(45, 45, 45, 240); border: 2px solid #00FF96; }

        """)

        self.setCursor(QCursor(Qt.PointingHandCursor))

        

        layout = QVBoxLayout()

        layout.setContentsMargins(15, 15, 15, 15)

        self.setLayout(layout)

        

        self.img_label = QLabel()

        self.img_label.setFixedSize(260, 145)

        self.img_label.setStyleSheet("border: none; background: transparent;")

        self.img_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.img_label)

        

        name = vehicle_data.get("Vehicle Name", "Bilinmiyor")

        v_class = vehicle_data.get("Vehicle Class", "")

        
        self.name_label = QLabel(f"<center><span style='color: {Theme.PRIMARY}; font-size: 13pt; font-weight: bold;'>{name}</span><br><span style='color: {Theme.TEXT_SECONDARY}; font-size: 10pt;'>{v_class}</span></center>")

        self.name_label.setStyleSheet("border: none; background: transparent;")

        self.name_label.setWordWrap(True)

        self.name_label.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.name_label)

        

        layout.addStretch() 

        

        badges = get_smart_badges(vehicle_data)

        badge_layout = QHBoxLayout()

        badge_layout.setAlignment(Qt.AlignCenter)

        for text, color in badges[:2]:

            b = QLabel(text)

            b.setFont(QFont("Segoe UI", 8, QFont.Bold))

            b.setStyleSheet(f"background-color: {color}; color: white; border-radius: 4px; padding: 4px 8px; border: none;")

            badge_layout.addWidget(b)

        layout.addLayout(badge_layout)



    def set_image(self, pixmap):
        try: 
            self.img_label.setPixmap(pixmap.scaled(Layout.CARD_IMAGE_WIDTH, Layout.CARD_IMAGE_HEIGHT, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except RuntimeError: 
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton: 
            self.clicked.emit(self.vehicle_data)

    def contextMenuEvent(self, event):
        """Sağ tık menüsü - hızlı aksiyonlar"""
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ 
                background: {Theme.SURFACE}; 
                color: {Theme.TEXT_PRIMARY}; 
                padding: {Layout.SPACING_TINY}px; 
                border: 1px solid {Theme.BORDER_COLOR};
                border-radius: {Theme.RADIUS_SMALL}px;
            }}
            QMenu::item {{ 
                padding: {Layout.SPACING_SMALL}px {Layout.SPACING_LARGE}px; 
            }}
            QMenu::item:selected {{ 
                background: {Theme.PRIMARY}; 
                color: black; 
            }}
        """)
        
        name = self.vehicle_data.get("Vehicle Name", "")
        garage = load_garage()
        is_owned = name in garage
        
        # Garaj aksiyonu
        action_garage = QAction("✅ Garajdan Çıkar" if is_owned else "➕ Garaja Ekle", self)
        action_garage.triggered.connect(lambda: self._toggle_garage(name))
        menu.addAction(action_garage)
        
        menu.addSeparator()
        
        # Detay aksiyonu
        action_detail = QAction("🔍 Detayları Gör", self)
        action_detail.triggered.connect(lambda: self.clicked.emit(self.vehicle_data))
        menu.addAction(action_detail)
        
        menu.exec_(event.globalPos())
    
    def _toggle_garage(self, vehicle_name):
        """Garaj toggle ve UI güncelleme"""
        toggle_vehicle_ownership(vehicle_name)
        # Badge'leri güncelle
        badges = get_smart_badges(self.vehicle_data)
        # Not: Parent window refresh gerekebilir



# ==========================================

# 2. GALERİ PENCERESİ (GÜNCELLENDİ: SEKMELER + İSTATİSTİK)

# ==========================================

class GalleryWindow(QWidget):

    def __init__(self, db_data, image_cache):

        super().__init__()

        self.db_data = db_data

        self.filtered_data = db_data

        self.image_cache = image_cache

        self.items_per_page = 15

        self.current_page = 0

        self.threads = []

        

        # YENİ: Varsayılan sekme

        self.current_tab = "STORE" 
        self.vehicle_history = None  # main.py'den set edilecek

        

        self.all_classes = sorted(list(set(c.get("Vehicle Class", "") for c in db_data if c.get("Vehicle Class", ""))))
        self.all_manufacturers = sorted(list(set(c.get("Manufacturer", "") for c in db_data if c.get("Manufacturer", ""))))
        self.all_vendors = sorted(list(set(c.get("Acquisition", "") for c in db_data if c.get("Acquisition", ""))))

        # YENİ: Modifikasyon atölyelerini çıkar
        mod_set = set()
        for c in db_data:
            m_str = c.get("Modifications", "")
            if m_str and m_str not in ["Veri Yok", "Cannot be modified"]:
                # Virgülle ayrılmış olabilir
                parts = [p.strip() for p in m_str.split(",")]
                mod_set.update(parts)
        self.all_mods = sorted(list(mod_set))

        

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # 1. Ekran boyutlarını al
        screen = QApplication.primaryScreen().availableGeometry()
        
        # 2. Minimum ve maksimum boyutları hesapla
        min_width, min_height = 800, 600
        # Maksimum boyut ekranın %90'ı (resize için alan bırak)
        max_width = int(screen.width() * 0.9)
        max_height = int(screen.height() * 0.9)
        
        self.setMinimumSize(min_width, min_height)
        self.setMaximumSize(max_width, max_height)
        
        # 3. Kayıtlı Geometriyi Al veya Varsayılanı Hesapla
        cfg = load_config()
        geom = cfg.get("ui_geometry", {}).get("GalleryWindow", {})
        
        # Varsayılan boyut ekranın %70'i (daha rahat başlangıç)
        default_width = min(1200, int(screen.width() * 0.7))
        default_height = min(800, int(screen.height() * 0.7))
        
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
        
        # Resizer'ı başlat
        self.resizer = FramelessResizer(self)

        self.setStyleSheet("""
            QWidget { font-family: 'Segoe UI', sans-serif; }
            QScrollBar:vertical { border: none; background: #2d3436; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #00FF96; border-radius: 4px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QMessageBox { background-color: #2d3436; color: white; }
            QMessageBox QLabel { color: white; }
            QMessageBox QPushButton { background-color: #0984e3; color: white; border-radius: 4px; padding: 6px 15px; }
        """)



        self.main_layout = QVBoxLayout()

        self.main_layout.setContentsMargins(10, 10, 10, 10)

        self.setLayout(self.main_layout)



        self.bg_frame = QFrame()

        self.bg_frame.setStyleSheet("""

            QFrame { background-color: rgba(18, 18, 18, 250); border: 2px solid #00FF96; border-radius: 15px; }

            QLineEdit { background: #2b2b2b; color: #FFF; padding: 10px 15px; border-radius: 6px; border: 1px solid #444; font-size: 11pt; font-weight: bold; }

            QLineEdit:focus { border: 1px solid #00FF96; }

            QComboBox { background: #2b2b2b; color: #FFF; padding: 10px 15px; border-radius: 6px; border: 1px solid #444; font-size: 11pt; font-weight: bold; }

            QComboBox:focus { border: 1px solid #00FF96; }
            
            QComboBox::drop-down { border: 0px; }
            
            QComboBox QAbstractItemView {
                background-color: #2b2b2b;
                color: white;
                selection-background-color: #00FF96;
                selection-color: black;
                border: 1px solid #444;
                outline: 0px;
            }

            QCheckBox { color: #FFF; font-weight: bold; font-size: 11pt; }

            QScrollBar:vertical { background: #1a1a1a; width: 12px; margin: 0px; border-radius: 6px;}

            QScrollBar::handle:vertical { background: #00FF96; min-height: 20px; border-radius: 6px;}

            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

        """)

        # ÖNEMLİ: bg_frame'i doğrudan eklemek yerine, kenarlarda resizer için boşluk bırakıyoruz
        self.main_layout.addWidget(self.bg_frame)
        self.main_layout.setContentsMargins(15, 15, 15, 15) # 15px Resize Zone (daha geniş)
        
        # Mouse tracking her yerde aktif
        self.setMouseTracking(True)
        self.bg_frame.setMouseTracking(True)
        
        self.bg_layout = QVBoxLayout(self.bg_frame)
        self.bg_layout.setContentsMargins(25, 25, 25, 25)

        self.stacked_widget = QStackedWidget()
        self.bg_layout.addWidget(self.stacked_widget)



        self.setup_gallery_page()

        self.setup_detail_page()

        self.setup_analytics_page()

        self.setup_history_page()

        
        # YENİ: Başlangıç ayarları
        self.settings_window = SettingsWindow()
        self.settings_window.hide()
        
        # Pagination başlangıç değerleri
        self.total_pages = 1
        
        # Tab Order Tanımla (Klavye navigasyonu için)
        self.setTabOrder(self.search_box, self.sort_box)
        self.setTabOrder(self.sort_box, self.class_box)
        self.setTabOrder(self.class_box, self.brand_box)
        self.setTabOrder(self.brand_box, self.vendor_box)
        self.setTabOrder(self.vendor_box, self.mod_box)
        self.setTabOrder(self.mod_box, self.armor_check)
        self.setTabOrder(self.armor_check, self.weapon_check)
        
        self.update_tab_buttons()
        self.apply_filters() 

    def mousePressEvent(self, event):
        self.resizer.handle_mouse_press(event)

    def mouseMoveEvent(self, event):
        self.resizer.handle_mouse_move(event)

    def mouseReleaseEvent(self, event):
        self.resizer.handle_mouse_release(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if hasattr(self, "grid_layout"):
            self.load_page()

    def closeEvent(self, event):
        """Pencere kapandığında boyut ve konumu kaydet."""
        self._save_geometry()
        super().closeEvent(event)
    
    def hideEvent(self, event):
        """Pencere gizlendiğinde de boyut ve konumu kaydet."""
        self._save_geometry()
        super().hideEvent(event)
    
    def _save_geometry(self):
        """Pencere geometrisini config'e kaydet."""
        cfg = load_config()
        if "ui_geometry" not in cfg: 
            cfg["ui_geometry"] = {}
        
        geom = self.geometry()
        cfg["ui_geometry"]["GalleryWindow"] = {
            "width": geom.width(),
            "height": geom.height(),
            "x": geom.x(),
            "y": geom.y()
        }
        save_config(cfg)



    def keyPressEvent(self, event):

        if event.key() == Qt.Key_Escape: self.hide()

        else: super().keyPressEvent(event)



    # YENİ: Sekme Değiştirme

    def switch_tab(self, mode):

        self.current_tab = mode

        self.update_tab_buttons()

        

        if mode == "GARAGE":

            count, value = get_garage_stats(self.db_data)

            self.stats_label.setText(f"💰 TOPLAM GARAJ DEĞERİ: <span style='color:#fdcb6e;'>{value}</span> &nbsp;&nbsp;|&nbsp;&nbsp; 🏎️ ARAÇ SAYISI: <span style='color:#00FF96;'>{count}</span>")

            self.stats_label.show()
            self.stacked_widget.setCurrentIndex(0)

        elif mode == "ANALYTICS":
            self.stats_label.hide()
            self.refresh_analytics()
            self.stacked_widget.setCurrentIndex(2)

        elif mode == "HISTORY":
            self.stats_label.hide()
            self.refresh_history()
            self.stacked_widget.setCurrentIndex(3)

        else:

            self.stats_label.hide()
            self.stacked_widget.setCurrentIndex(0)

            

        if mode in ("STORE", "GARAGE"):
            self.apply_filters()



    # YENİ: Buton Renklerini Güncelleme

    def update_tab_buttons(self):

        active_style = "background: #00FF96; color: black; font-weight: bold; padding: 10px; border-radius: 6px; font-size: 11pt;"

        passive_style = "background: #2b2b2b; color: white; font-weight: bold; padding: 10px; border-radius: 6px; font-size: 11pt; border: 1px solid #444;"

        
        for btn, tab_id in [(self.btn_store, "STORE"), (self.btn_garage, "GARAGE"), (self.btn_analytics, "ANALYTICS"), (self.btn_history, "HISTORY")]:
            btn.setStyleSheet(active_style if self.current_tab == tab_id else passive_style)



    def setup_gallery_page(self):

        page = QWidget()

        layout = QVBoxLayout(page)

        layout.setContentsMargins(0, 0, 0, 0)

        

        # --- YENİ: Sekme Butonları ---

        tabs_layout = QHBoxLayout()

        tabs_layout.setSpacing(15)

        

        self.btn_store = QPushButton("🛒 MAĞAZA (TÜM ARAÇLAR)")

        self.btn_store.setCursor(QCursor(Qt.PointingHandCursor))

        self.btn_store.clicked.connect(lambda: self.switch_tab("STORE"))

        tabs_layout.addWidget(self.btn_store)

        

        self.btn_garage = QPushButton("🏠 GARAJIM")

        self.btn_garage.setCursor(QCursor(Qt.PointingHandCursor))

        self.btn_garage.clicked.connect(lambda: self.switch_tab("GARAGE"))

        tabs_layout.addWidget(self.btn_garage)

        
        self.btn_analytics = QPushButton("📊 ANALİTİK")
        self.btn_analytics.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_analytics.clicked.connect(lambda: self.switch_tab("ANALYTICS"))
        tabs_layout.addWidget(self.btn_analytics)

        self.btn_history = QPushButton("🕐 GEÇMİŞ")
        self.btn_history.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_history.clicked.connect(lambda: self.switch_tab("HISTORY"))
        tabs_layout.addWidget(self.btn_history)

        layout.addLayout(tabs_layout)

        # -----------------------------



        # --- YENİ: İstatistik Barı ---

        self.stats_label = QLabel("Yükleniyor...")

        self.stats_label.setAlignment(Qt.AlignCenter)

        self.stats_label.setStyleSheet("""

            background-color: #2d3436; 

            color: white; 

            font-size: 12pt; 

            font-weight: bold; 

            padding: 8px; 

            border-radius: 6px; 

            border: 1px solid #636e72;

            margin-top: 5px;

            margin-bottom: 5px;

        """)

        self.stats_label.hide()

        layout.addWidget(self.stats_label)

        # -----------------------------

        

        top_bar_1 = QHBoxLayout()
        top_bar_1.setSpacing(15)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Araç Ara (Örn: Zentorno, T20)...")
        self.search_box.setToolTip("Araç ismi veya markasına göre arama yapın")
        self.search_box.setAccessibleName("Araç Arama Kutusu")
        self.search_box.textChanged.connect(self.apply_filters)
        top_bar_1.addWidget(self.search_box, stretch=2)

        self.sort_box = QComboBox()
        self.sort_box.addItems(["Sıralama: Varsayılan", "Fiyat: Önce En Pahalı", "Fiyat: Önce En Ucuz", "Hız: En Hızlılar", "İvme: En Yüksek Kalkış"])
        self.sort_box.setToolTip("Araçları farklı kriterlere göre sıralayın")
        self.sort_box.setAccessibleName("Sıralama Seçenekleri")
        self.sort_box.currentTextChanged.connect(self.apply_filters)
        top_bar_1.addWidget(self.sort_box, stretch=1)

        close_btn = QPushButton("KAPAT (F11)")
        close_btn.setCursor(QCursor(Qt.PointingHandCursor))
        close_btn.setToolTip("Galeriyi kapat (F11)")
        close_btn.setAccessibleName("Galeriyi Kapat")
        close_btn.setStyleSheet("background: #d63031; color: white; padding: 10px 20px; border-radius: 6px; font-weight:bold; font-size: 11pt;")
        close_btn.clicked.connect(self.hide)
        top_bar_1.addWidget(close_btn)

        settings_btn = QPushButton("⚙️ AYARLAR")
        settings_btn.setCursor(QCursor(Qt.PointingHandCursor))
        settings_btn.setToolTip("Uygulama ayarlarını aç")
        settings_btn.setAccessibleName("Ayarlar Menüsü")
        settings_btn.setAccessibleDescription("OCR bölgesi, kısayol tuşları ve diğer ayarları değiştirin")
        settings_btn.setStyleSheet("background: #636e72; color: white; padding: 10px 20px; border-radius: 6px; font-weight:bold; font-size: 11pt;")
        settings_btn.clicked.connect(self.open_settings)
        top_bar_1.addWidget(settings_btn)

        layout.addLayout(top_bar_1)

        
        top_bar_2 = QHBoxLayout()
        top_bar_2.setSpacing(15)

        self.class_box = QComboBox()
        self.class_box.addItem("Tüm Sınıflar")
        self.class_box.addItems(self.all_classes)
        self.class_box.setToolTip("Araçları sınıfına göre filtrele (Sports, Super, SUV vb.)")
        self.class_box.setAccessibleName("Araç Sınıfı Filtresi")
        self.class_box.currentTextChanged.connect(self.apply_filters)
        top_bar_2.addWidget(self.class_box)

        self.brand_box = QComboBox()
        self.brand_box.addItem("Tüm Markalar")
        self.brand_box.addItems(self.all_manufacturers)
        self.brand_box.setToolTip("Araçları markasına göre filtrele")
        self.brand_box.setAccessibleName("Marka Filtresi")
        self.brand_box.currentTextChanged.connect(self.apply_filters)
        top_bar_2.addWidget(self.brand_box)

        self.vendor_box = QComboBox()
        self.vendor_box.addItem("Tüm Satıcılar")
        self.vendor_box.addItems(self.all_vendors)
        self.vendor_box.setToolTip("Araçları satıcısına göre filtrele")
        self.vendor_box.setAccessibleName("Satıcı Filtresi")
        self.vendor_box.currentTextChanged.connect(self.apply_filters)
        top_bar_2.addWidget(self.vendor_box)

        # YENİ: Modifikasyon Filtresi
        self.mod_box = QComboBox()
        self.mod_box.addItem("Tüm Atölyeler")
        self.mod_box.addItems(self.all_mods)
        self.mod_box.setToolTip("Araçları modifikasyon atölyesine göre filtrele")
        self.mod_box.setAccessibleName("Atölye Filtresi")
        self.mod_box.currentTextChanged.connect(self.apply_filters)
        top_bar_2.addWidget(self.mod_box)

        self.armor_check = QCheckBox("Sadece Zırhlı")
        self.armor_check.setCursor(QCursor(Qt.PointingHandCursor))
        self.armor_check.setToolTip("Sadece zırh özelliği olan araçları göster")
        self.armor_check.setAccessibleName("Zırh Filtresi")
        self.armor_check.stateChanged.connect(self.apply_filters)
        top_bar_2.addWidget(self.armor_check)

        self.weapon_check = QCheckBox("Sadece Silahlı")
        self.weapon_check.setCursor(QCursor(Qt.PointingHandCursor))
        self.weapon_check.setToolTip("Sadece silah özelliği olan araçları göster")
        self.weapon_check.setAccessibleName("Silah Filtresi")
        self.weapon_check.stateChanged.connect(self.apply_filters)
        top_bar_2.addWidget(self.weapon_check)

        # Filtre Temizleme Butonu
        clear_filters_btn = QPushButton("🔄 Filtreleri Temizle")
        clear_filters_btn.setCursor(QCursor(Qt.PointingHandCursor))
        clear_filters_btn.setToolTip("Tüm filtreleri varsayılan değerlere döndür")
        clear_filters_btn.setAccessibleName("Filtreleri Temizle")
        clear_filters_btn.setStyleSheet(f"""
            QPushButton {{
                background: {Theme.WARNING};
                color: black;
                padding: 8px 15px;
                border-radius: {Theme.RADIUS_SMALL}px;
                font-weight: bold;
                font-size: 10pt;
            }}
            QPushButton:hover {{
                background: {Theme.PRIMARY};
            }}
        """)
        clear_filters_btn.clicked.connect(self.clear_filters)
        top_bar_2.addWidget(clear_filters_btn)

        layout.addLayout(top_bar_2)

        

        self.gallery_scroll = QScrollArea()

        self.gallery_scroll.setWidgetResizable(True)

        self.gallery_scroll.setStyleSheet("background: transparent; border: none;")

        self.grid_widget = QWidget()

        self.grid_widget.setStyleSheet("background: transparent;")

        self.grid_layout = QGridLayout(self.grid_widget)

        self.grid_layout.setSpacing(15) 

        self.grid_layout.setAlignment(Qt.AlignTop)

        self.gallery_scroll.setWidget(self.grid_widget)

        layout.addWidget(self.gallery_scroll)

        

        bottom_bar = QHBoxLayout()

        # Pagination Controls
        self.prev_btn = QPushButton("<< ÖNCEKİ SAYFA")
        self.prev_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.prev_btn.setToolTip("Önceki sayfaya git")
        self.prev_btn.setAccessibleName("Önceki Sayfa")
        self.prev_btn.setStyleSheet("background: #2b2b2b; color: white; padding: 10px 20px; border-radius: 6px; font-weight:bold; font-size: 11pt;")
        self.prev_btn.clicked.connect(lambda: self.change_page(-1))
        bottom_bar.addWidget(self.prev_btn)

        # İlk Sayfa Butonu
        self.first_page_btn = QPushButton("|◀ İLK")
        self.first_page_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.first_page_btn.setToolTip("İlk sayfaya git")
        self.first_page_btn.setAccessibleName("İlk Sayfa")
        self.first_page_btn.setStyleSheet("background: #2b2b2b; color: white; padding: 10px 15px; border-radius: 6px; font-weight:bold; font-size: 10pt;")
        self.first_page_btn.clicked.connect(lambda: self.go_to_page(0))
        bottom_bar.addWidget(self.first_page_btn)

        self.page_label = QLabel("Sayfa 1 / 1")
        self.page_label.setStyleSheet("color: #00FF96; font-weight: bold; font-size: 14pt;")
        self.page_label.setAlignment(Qt.AlignCenter)
        bottom_bar.addWidget(self.page_label)

        # Sayfa Numarası Input
        page_input_layout = QHBoxLayout()
        page_input_label = QLabel("Sayfa:")
        page_input_label.setStyleSheet("color: white; font-size: 10pt;")
        self.page_input = QSpinBox()
        self.page_input.setMinimum(1)
        self.page_input.setMaximum(1)
        self.page_input.setToolTip("Belirli bir sayfaya git")
        self.page_input.setAccessibleName("Sayfa Numarası")
        self.page_input.setStyleSheet("""
            QSpinBox {
                background: #2b2b2b;
                color: white;
                padding: 5px;
                border: 1px solid #444;
                border-radius: 4px;
                font-size: 10pt;
            }
        """)
        self.page_input.valueChanged.connect(lambda val: self.go_to_page(val - 1))
        page_input_layout.addWidget(page_input_label)
        page_input_layout.addWidget(self.page_input)
        bottom_bar.addLayout(page_input_layout)

        # Son Sayfa Butonu
        self.last_page_btn = QPushButton("SON ▶|")
        self.last_page_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.last_page_btn.setToolTip("Son sayfaya git")
        self.last_page_btn.setAccessibleName("Son Sayfa")
        self.last_page_btn.setStyleSheet("background: #2b2b2b; color: white; padding: 10px 15px; border-radius: 6px; font-weight:bold; font-size: 10pt;")
        self.last_page_btn.clicked.connect(lambda: self.go_to_page(self.total_pages - 1))
        bottom_bar.addWidget(self.last_page_btn)

        self.next_btn = QPushButton("SONRAKİ SAYFA >>")
        self.next_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.next_btn.setToolTip("Sonraki sayfaya git")
        self.next_btn.setAccessibleName("Sonraki Sayfa")
        self.next_btn.setStyleSheet("background: #00FF96; color: black; padding: 10px 20px; border-radius: 6px; font-weight:bold; font-size: 11pt;")
        self.next_btn.clicked.connect(lambda: self.change_page(1))
        bottom_bar.addWidget(self.next_btn)

        layout.addLayout(bottom_bar)

        self.stacked_widget.addWidget(page)



    def setup_detail_page(self):

        page = QWidget()

        layout = QVBoxLayout(page)

        top_bar = QHBoxLayout()

        back_btn = QPushButton("<< GALERİYE DÖN")

        back_btn.setCursor(QCursor(Qt.PointingHandCursor))

        back_btn.setStyleSheet("background: #00FF96; color: black; font-weight: bold; padding: 10px 20px; border-radius: 6px; font-size: 11pt;")

        back_btn.clicked.connect(lambda: self.stacked_widget.setCurrentIndex(0))

        top_bar.addWidget(back_btn)

        top_bar.addStretch()

        layout.addLayout(top_bar)

        self.detail_scroll = QScrollArea()

        self.detail_scroll.setWidgetResizable(True)

        self.detail_scroll.setStyleSheet("background: transparent; border: none;")

        self.detail_content = QWidget()

        self.detail_layout = QVBoxLayout(self.detail_content)

        self.detail_title = QLabel()

        self.detail_title.setAlignment(Qt.AlignCenter)

        self.detail_layout.addWidget(self.detail_title)

        self.detail_img = QLabel()

        self.detail_img.setAlignment(Qt.AlignCenter)

        self.detail_img.setAlignment(Qt.AlignCenter)
        self.detail_layout.addWidget(self.detail_img)
        
        self.detail_badges = FlowLayout()
        # self.detail_badges.setAlignment(Qt.AlignCenter) # FlowLayout hizalaması farklı çalışır
        self.detail_layout.addLayout(self.detail_badges)
        
        self.detail_stats = QGridLayout()

        self.detail_stats.setSpacing(10)

        self.detail_layout.addLayout(self.detail_stats)

        self.detail_scroll.setWidget(self.detail_content)

        layout.addWidget(self.detail_scroll)

        self.stacked_widget.addWidget(page)



    def apply_filters(self):

        query = self.search_box.text().lower()

        v_class = self.class_box.currentText()
        brand = self.brand_box.currentText()
        vendor = self.vendor_box.currentText()
        mod_type = self.mod_box.currentText()
        req_armor = self.armor_check.isChecked()
        req_weapon = self.weapon_check.isChecked()

        sort_mode = self.sort_box.currentText()

        

        # YENİ: Garaj listesini çek

        owned_list = load_garage()

        

        self.filtered_data = []

        for car in self.db_data:

            # YENİ: Garaj modundaysa sadece sahip olunanları göster

            if self.current_tab == "GARAGE":

                if car.get("Vehicle Name") not in owned_list:

                    continue

            

            match_query = query in car.get("Vehicle Name", "").lower()

            match_class = (v_class == "Tüm Sınıflar") or (v_class == car.get("Vehicle Class", ""))

            match_brand = (brand == "Tüm Markalar") or (brand == car.get("Manufacturer", ""))

            match_vendor = (vendor == "Tüm Satıcılar") or (vendor == car.get("Acquisition", ""))
            match_mod = (mod_type == "Tüm Atölyeler") or (mod_type in str(car.get("Modifications", "")))
            match_armor = True
            if req_armor: match_armor = "Yes" in str(car.get("Bulletproof", ""))
            match_weapon = True
            if req_weapon: match_weapon = "Weaponized" in str(car.get("Vehicle Features", ""))
            
            if match_query and match_class and match_brand and match_vendor and match_mod and match_armor and match_weapon:

                self.filtered_data.append(car)

        

        if sort_mode == "Fiyat: Önce En Pahalı":

            self.filtered_data.sort(key=lambda x: parse_number(x.get("GTA Online Price", "0")), reverse=True)

        elif sort_mode == "Fiyat: Önce En Ucuz":

            self.filtered_data.sort(key=lambda x: parse_number(x.get("GTA Online Price", "0")))

        elif sort_mode == "Hız: En Hızlılar":

            self.filtered_data.sort(key=lambda x: parse_number(x.get("Top Speed (Broughy)", "0")), reverse=True)

        elif sort_mode == "İvme: En Yüksek Kalkış":

            self.filtered_data.sort(key=lambda x: parse_number(x.get("Stat - Acceleration", "0")), reverse=True)

        

        self.current_page = 0

        self.load_page()



    def load_page(self):
        self.threads = [t for t in self.threads if t.isRunning()]

        for i in reversed(range(self.grid_layout.count())): 
            w = self.grid_layout.itemAt(i).widget()
            if w: w.deleteLater()

        self.total_pages = max(1, (len(self.filtered_data) + self.items_per_page - 1) // self.items_per_page)
        
        # Sayfa limitlerini kontrol et
        if self.current_page >= self.total_pages:
            self.current_page = self.total_pages - 1
        if self.current_page < 0:
            self.current_page = 0

        self.page_label.setText(f"Sayfa {self.current_page + 1} / {self.total_pages}")

        # Butonları enable/disable
        self.prev_btn.setEnabled(self.current_page > 0)
        self.first_page_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < self.total_pages - 1)
        self.last_page_btn.setEnabled(self.current_page < self.total_pages - 1)
        
        # Sayfa input'u güncelle
        self.page_input.setMaximum(self.total_pages)
        self.page_input.blockSignals(True)  # Sonsuz loop önleme
        self.page_input.setValue(self.current_page + 1)
        self.page_input.blockSignals(False)

        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        page_items = self.filtered_data[start_idx:end_idx]

        # Dinamik Sütun Hesaplama
        available_width = self.gallery_scroll.width() - 40
        card_width = 310 # 290 px kart + 20 px boşluk
        cols = max(1, available_width // card_width)
        
        # Sütun sayısına göre items_per_page'i ayarla (Opsiyonel, şimdilik sabit 15)
        # self.items_per_page = cols * 3 

        row, col = 0, 0

        for car in page_items:
            card = VehicleCard(car)
            card.clicked.connect(self.show_detail)
            self.grid_layout.addWidget(card, row, col)

            url = car.get("Image URL", "")

            if url in self.image_cache:
                card.set_image(self.image_cache[url])

            elif url and url != "Resim Bulunamadı":
                thread = ImageLoaderThread(url)
                thread.image_loaded_signal.connect(lambda u, p, c=card: self.cache_and_set(u, p, c))
                self.threads.append(thread)
                thread.start()

            col += 1
            if col >= cols: 
                col = 0
                row += 1



    def cache_and_set(self, url, qimage, card):
        """QImage'i QPixmap'e dönüştürüp cache'e ekler (Ana thread'de çalışır)."""
        pixmap = QPixmap.fromImage(qimage)  # Ana thread'de dönüştür
        self.image_cache[url] = pixmap
        try: 
            card.set_image(pixmap)
        except RuntimeError: 
            pass



    def change_page(self, delta):
        self.current_page += delta
        self.load_page()

    def go_to_page(self, page_num):
        """Belirli bir sayfaya git"""
        if 0 <= page_num < self.total_pages:
            self.current_page = page_num
            self.load_page()

    def clear_filters(self):
        """Tüm filtreleri varsayılan değerlere döndür"""
        self.search_box.clear()
        self.sort_box.setCurrentIndex(0)
        self.class_box.setCurrentIndex(0)
        self.brand_box.setCurrentIndex(0)
        self.vendor_box.setCurrentIndex(0)
        self.mod_box.setCurrentIndex(0)
        self.armor_check.setChecked(False)
        self.weapon_check.setChecked(False)
        self.apply_filters()

    def keyPressEvent(self, event):
        """Klavye navigasyonu desteği"""
        if event.key() == Qt.Key_Escape:
            self.hide()
        elif event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Enter ile arama kutusundan filtre uygula
            focused = QApplication.focusWidget()
            if focused == self.search_box:
                self.apply_filters()
        elif event.key() == Qt.Key_Left:
            # Sol ok - önceki sayfa
            if self.current_page > 0:
                self.change_page(-1)
        elif event.key() == Qt.Key_Right:
            # Sağ ok - sonraki sayfa
            if self.current_page < self.total_pages - 1:
                self.change_page(1)
        else:
            super().keyPressEvent(event)



    def show_detail(self, vehicle_data):

        self.stacked_widget.setCurrentIndex(1)

        name = vehicle_data.get("Vehicle Name", "")

        v_class = vehicle_data.get("Vehicle Class", "")

        self.detail_title.setText(f"<span style='font-size:24pt; color:#00FF96; font-weight:bold;'>{name.upper()}</span><br><span style='color:#AAA; font-size:14pt;'>{v_class}</span>")

        url = vehicle_data.get("Image URL", "")

        self.detail_img.clear()

        if url in self.image_cache:

            self.detail_img.setPixmap(self.image_cache[url].scaled(600, 350, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        for i in reversed(range(self.detail_badges.count())): 

            w = self.detail_badges.itemAt(i).widget()

            if w: w.deleteLater()

        for text, color in get_smart_badges(vehicle_data):

            b = QLabel(text)

            b.setFont(QFont("Segoe UI", 12, QFont.Bold))

            b.setStyleSheet(f"background-color: {color}; color: white; border-radius: 6px; padding: 6px 15px; margin: 10px;")

            self.detail_badges.addWidget(b)

        for i in reversed(range(self.detail_stats.count())): 

            w = self.detail_stats.itemAt(i).widget()

            if w: w.deleteLater()

        row = 0

        exclude_keys = ["Vehicle Name", "Vehicle Class", "Link", "Image URL", "Variants", "Liveries"]

        for key, value in vehicle_data.items():

            if key not in exclude_keys and value and value != "Veri Yok":

                lbl_title = QLabel(f"{key}:")

                lbl_title.setFont(QFont("Segoe UI", 12, QFont.Bold)) 

                lbl_title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; padding: 5px;")

                lbl_value = QLabel(str(value))

                lbl_value.setFont(QFont("Segoe UI", 12)) 

                lbl_value.setStyleSheet("color: #FFFFFF; padding: 5px;")

                lbl_value.setWordWrap(True)

                self.detail_stats.addWidget(lbl_title, row, 0)

                self.detail_stats.addWidget(lbl_value, row, 1)
                row += 1

    def open_settings(self):
        self.hide()
        self.settings_window = SettingsWindow(parent=self)
        self.settings_window.show()

    # === ANALİTİK SAYFA ===
    def setup_analytics_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Başlık
        title = QLabel("📊 GARAJ ANALİTİKLERİ")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #00FF96;")
        layout.addWidget(title)

        # Scroll Area içinde içerik
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        self.analytics_content = QWidget()
        self.analytics_layout = QVBoxLayout(self.analytics_content)
        self.analytics_layout.setSpacing(15)
        scroll.setWidget(self.analytics_content)
        layout.addWidget(scroll)

        # Geri Butonu
        back_btn = QPushButton("⬅ MAĞAZAYA DÖN")
        back_btn.setCursor(QCursor(Qt.PointingHandCursor))
        back_btn.setStyleSheet("background: #636e72; color: white; padding: 10px; font-weight: bold; border-radius: 6px; font-size: 11pt;")
        back_btn.clicked.connect(lambda: self.switch_tab("STORE"))
        layout.addWidget(back_btn)

        self.stacked_widget.addWidget(page)  # index 2

    def refresh_analytics(self):
        # Temizle
        for i in reversed(range(self.analytics_layout.count())):
            w = self.analytics_layout.itemAt(i).widget()
            if w: w.deleteLater()

        garage = load_garage()
        garage_vehicles = [v for v in self.db_data if v.get("Vehicle Name", "") in garage]
        total_value = sum(parse_number(v.get("GTA Online Price", "0")) for v in garage_vehicles)

        # === Özet Kutusu ===
        summary_frame = QFrame()
        summary_frame.setStyleSheet("background: #2d3436; border-radius: 10px; padding: 15px;")
        summary_layout = QGridLayout(summary_frame)

        stats = [
            ("🏎️ Toplam Araç", str(len(garage)), "#00FF96"),
            ("💰 Toplam Değer", f"${total_value:,.0f}", "#fdcb6e"),
        ]

        if garage_vehicles:
            most_expensive = max(garage_vehicles, key=lambda v: parse_number(v.get("GTA Online Price", "0")))
            fastest = max(garage_vehicles, key=lambda v: parse_number(v.get("Top Speed (Broughy)", "0")))
            stats.append(("💵 En Pahalı", most_expensive.get("Vehicle Name", ""), "#e17055"))
            stats.append(("⚡ En Hızlı", fastest.get("Vehicle Name", ""), "#74b9ff"))

        for i, (label_text, value_text, color) in enumerate(stats):
            lbl = QLabel(f"<span style='color: {Theme.TEXT_SECONDARY}; font-size: 10pt;'>{label_text}</span><br>"
                         f"<span style='color: {color}; font-size: 14pt; font-weight: bold;'>{value_text}</span>")
            lbl.setAlignment(Qt.AlignCenter)
            summary_layout.addWidget(lbl, 0, i)

        self.analytics_layout.addWidget(summary_frame)

        # === Sınıf Dağılımı ===
        class_frame = QFrame()
        class_frame.setStyleSheet("background: #2d3436; border-radius: 10px; padding: 15px;")
        class_layout = QVBoxLayout(class_frame)

        class_title = QLabel("📊 Sınıf Dağılımı")
        class_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        class_title.setStyleSheet("color: #00FF96; margin-bottom: 10px;")
        class_layout.addWidget(class_title)

        # Sınıf sayılarını hesapla
        class_counts = {}
        for v in garage_vehicles:
            vc = v.get("Vehicle Class", "Bilinmiyor")
            class_counts[vc] = class_counts.get(vc, 0) + 1

        # En çoktan aza sırala
        sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
        max_count = sorted_classes[0][1] if sorted_classes else 1

        for cls_name, count in sorted_classes:
            row = QHBoxLayout()
            lbl = QLabel(f"{cls_name}")
            lbl.setFixedWidth(150)
            lbl.setStyleSheet("color: white; font-size: 10pt;")
            row.addWidget(lbl)

            # Bar
            bar_width = int((count / max_count) * 100)
            bar = QFrame()
            bar.setFixedHeight(20)
            bar.setFixedWidth(max(bar_width * 4, 20))
            bar.setStyleSheet("background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00FF96, stop:1 #00b894); border-radius: 4px;")
            row.addWidget(bar)

            count_lbl = QLabel(f" {count}")
            count_lbl.setStyleSheet("color: #00FF96; font-weight: bold; font-size: 10pt;")
            row.addWidget(count_lbl)
            row.addStretch()
            class_layout.addLayout(row)

        self.analytics_layout.addWidget(class_frame)

        # === Eksik Sınıflar ===
        all_classes = set(v.get("Vehicle Class", "") for v in self.db_data if v.get("Vehicle Class", ""))
        owned_classes = set(class_counts.keys())
        missing = all_classes - owned_classes

        if missing:
            missing_frame = QFrame()
            missing_frame.setStyleSheet("background: #2d3436; border-radius: 10px; padding: 15px;")
            missing_layout = QVBoxLayout(missing_frame)

            missing_title = QLabel(f"❌ Eksik Sınıflar ({len(missing)})")
            missing_title.setFont(QFont("Segoe UI", 12, QFont.Bold))
            missing_title.setStyleSheet("color: #d63031; margin-bottom: 10px;")
            missing_layout.addWidget(missing_title)

            flow = FlowLayout(spacing=8)
            for cls in sorted(missing):
                tag = QLabel(cls)
                tag.setFont(QFont("Segoe UI", 9))
                tag.setStyleSheet("background: #636e72; color: white; padding: 5px 10px; border-radius: 4px;")
                flow.addWidget(tag)
            missing_layout.addLayout(flow)
            self.analytics_layout.addWidget(missing_frame)

        self.analytics_layout.addStretch()

    # === GEÇMİŞ SAYFA ===
    def setup_history_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Başlık
        title = QLabel("🕐 SON GÖRÜLEN ARAÇLAR")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title.setStyleSheet("color: #00FF96;")
        layout.addWidget(title)

        # İstatistik barı
        self.history_stats_label = QLabel("")
        self.history_stats_label.setAlignment(Qt.AlignCenter)
        self.history_stats_label.setStyleSheet("background: #2d3436; color: white; font-size: 11pt; font-weight: bold; padding: 8px; border-radius: 6px; border: 1px solid #636e72;")
        layout.addWidget(self.history_stats_label)

        # Scroll Area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        self.history_content = QWidget()
        self.history_layout = QVBoxLayout(self.history_content)
        self.history_layout.setSpacing(8)
        scroll.setWidget(self.history_content)
        layout.addWidget(scroll)

        # Geri Butonu
        back_btn = QPushButton("⬅ MAĞAZAYA DÖN")
        back_btn.setCursor(QCursor(Qt.PointingHandCursor))
        back_btn.setStyleSheet("background: #636e72; color: white; padding: 10px; font-weight: bold; border-radius: 6px; font-size: 11pt;")
        back_btn.clicked.connect(lambda: self.switch_tab("STORE"))
        layout.addWidget(back_btn)

        self.stacked_widget.addWidget(page)  # index 3

    def refresh_history(self):
        # Temizle
        for i in reversed(range(self.history_layout.count())):
            w = self.history_layout.itemAt(i).widget()
            if w: w.deleteLater()

        if not self.vehicle_history:
            empty = QLabel("Henüz hiç araç tespit edilmedi.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #636e72; font-size: 14pt; padding: 40px;")
            self.history_layout.addWidget(empty)
            self.history_stats_label.setText("📊 Henüz veri yok")
            return

        stats = self.vehicle_history.get_stats()
        recent = self.vehicle_history.get_recent(20)

        # İstatistik
        most_seen_text = f" | 🎯 En çok: {stats['most_seen']} ({stats['most_seen_count']}x)" if stats['most_seen'] else ""
        self.history_stats_label.setText(
            f"📊 Bugün: <span style='color:#00FF96;'>{stats['daily']}</span> araç | "
            f"Toplam: <span style='color:#fdcb6e;'>{stats['total']}</span> tespit | "
            f"Benzersiz: <span style='color:#74b9ff;'>{stats['unique']}</span>{most_seen_text}"
        )

        if not recent:
            empty = QLabel("Henüz hiç araç tespit edilmedi.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet("color: #636e72; font-size: 14pt; padding: 40px;")
            self.history_layout.addWidget(empty)
            return

        for entry in recent:
            row_frame = QFrame()
            row_frame.setStyleSheet("background: #2d3436; border-radius: 8px; padding: 8px;")
            row_layout = QHBoxLayout(row_frame)
            row_layout.setContentsMargins(10, 5, 10, 5)

            # Saat
            time_lbl = QLabel(entry["time_str"])
            time_lbl.setFixedWidth(70)
            time_lbl.setFont(QFont("Consolas", 10))
            time_lbl.setStyleSheet("color: #636e72;")
            row_layout.addWidget(time_lbl)

            # Araç İsmi
            name_lbl = QLabel(entry["name"])
            name_lbl.setFont(QFont("Segoe UI", 11, QFont.Bold))
            name_lbl.setStyleSheet("color: #00FF96;")
            row_layout.addWidget(name_lbl)

            # Sınıf
            v_class = entry["data"].get("Vehicle Class", "")
            if v_class:
                class_lbl = QLabel(v_class)
                class_lbl.setFont(QFont("Segoe UI", 9))
                class_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
                row_layout.addWidget(class_lbl)

            # Fiyat
            price_str = entry["data"].get("GTA Online Price", "")
            if price_str and price_str != "Veri Yok":
                price_lbl = QLabel(str(price_str))
                price_lbl.setFont(QFont("Segoe UI", 9))
                price_lbl.setStyleSheet("color: #fdcb6e;")
                row_layout.addWidget(price_lbl)

            row_layout.addStretch()

            # Detay butonu
            detail_btn = QPushButton("🔍")
            detail_btn.setFixedSize(30, 30)
            detail_btn.setCursor(QCursor(Qt.PointingHandCursor))
            detail_btn.setStyleSheet("background: #636e72; color: white; border-radius: 4px; font-size: 12pt;")
            vehicle_data = entry["data"]
            detail_btn.clicked.connect(lambda checked, vd=vehicle_data: self.show_detail(vd))
            row_layout.addWidget(detail_btn)

            self.history_layout.addWidget(row_frame)

        self.history_layout.addStretch()


# ==========================================
# 6. SCROLLING LABEL (KAYAN YAZI)
# ==========================================
class ScrollingLabel(QWidget):
    def __init__(self, text, parent=None, font_size=10, color="white"):
        super().__init__(parent)
        self._text = text
        self._offset = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.scroll_text)
        self.setFont(QFont("Segoe UI", font_size, QFont.Bold))
        self.setFixedHeight(30) # Sabit yükseklik
        
        # Renk ayarı
        self.color = color
        
        # Metin Genişliği Hesabı
        font_metrics = QFontMetrics(self.font())
        self.text_width = font_metrics.width(self._text)
        
        # Sadece metin sığmıyorsa kaydır
        self.should_scroll = False

    def showEvent(self, event):
        """Widget ilk gösterildiğinde kaydırma kontrolü yap."""
        super().showEvent(event)
        if self.width() > 0 and self.width() < self.text_width:
            self.should_scroll = True
            if not self.timer.isActive():
                self.timer.start(30)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QColor(self.color))
        painter.setFont(self.font())
        
        if not self.should_scroll:
            # Sığıyorsa normal çiz (Sola hizalı)
            painter.drawText(self.rect(), Qt.AlignLeft | Qt.AlignVCenter, self._text)
            return

        # Kayan Yazı Mantığı
        # Metni iki kere çiziyoruz ki kesintisiz dönsün
        painter.drawText(self._offset, 20, self._text)
        painter.drawText(self._offset + self.text_width + 50, 20, self._text) # 50px boşluk

    def scroll_text(self):
        self._offset -= 1 # Sola kaydır
        if abs(self._offset) >= self.text_width + 50:
            self._offset = 0 # Başa dön
        self.update()

    def resizeEvent(self, event):
        # Pencere boyutu değişince kaydırma gerekip gerekmediğini kontrol et
        if self.width() < self.text_width:
            self.should_scroll = True
            if not self.timer.isActive():
                self.timer.start(30) # 30ms'de bir güncelle
        else:
            self.should_scroll = False
            self.timer.stop()
            self._offset = 0
            self.update()

# ==========================================
# 7. DURUM GÖSTERGESİ (STATUS HUD)
# ==========================================
class StatusHUD(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.WindowTransparentForInput | 
            Qt.Tool | 
            Qt.WindowDoesNotAcceptFocus
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Ekranın üst ortasına yerleş (Daha kompakt)
        screen = QApplication.desktop().screenGeometry()
        width = 220 
        height = 32
        self.setGeometry((screen.width() - width) // 2, 8, width, height)

        self.layout = QHBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.frame = QFrame()
        self.frame.setStyleSheet("""
            background-color: rgba(15, 15, 15, 230); 
            border: 1px solid #00FF96; 
            border-radius: 15px;
        """)
        self.layout.addWidget(self.frame)

        # The original snippet had self.content_layout = QVBoxLayout(self.main_widget)
        # but self.main_widget does not exist in StatusHUD.
        # Assuming the intent was to apply margins to the main layout,
        # the change was applied to self.layout.setContentsMargins above.
        # If a new layout was intended to wrap the frame, it would need to be structured differently.

        self.inner_layout = QHBoxLayout(self.frame)
        self.inner_layout.setContentsMargins(15, 0, 15, 0)
        self.inner_layout.setSpacing(10)

        self.inner_layout.addStretch() # ORTALA İÇİN BAŞA DA KOYDUK

        # Jarvis Statüsü
        self.lbl_jarvis = QLabel("JARVIS")
        self.lbl_jarvis.setStyleSheet("color: #00FF96; font-weight: 900; font-family: 'Segoe UI'; font-size: 10pt;")
        self.inner_layout.addWidget(self.lbl_jarvis)

        # Ayırıcı Nokta
        dot = QLabel("•")
        dot.setStyleSheet("color: #555; font-size: 12pt;")
        self.inner_layout.addWidget(dot)

        # OCR Durumu
        self.lbl_ocr = QLabel("OCR: AÇIK")
        self.lbl_ocr.setStyleSheet("color: white; font-weight: bold; font-family: 'Segoe UI'; font-size: 9pt;")
        self.inner_layout.addWidget(self.lbl_ocr)

        # Buton Hint (F10) - Daha silik
        self.lbl_hint = QLabel("[F10]")
        self.lbl_hint.setStyleSheet("color: #777; font-size: 8pt; font-family: 'Consolas'; margin-left: 5px;")
        self.inner_layout.addWidget(self.lbl_hint)
        
        self.inner_layout.addStretch()
        
        # Config Yükle
        self.update_shortcut_text()

    def update_shortcut_text(self):
        try:
            cfg = load_config()
            hk = cfg.get("hotkeys", {}).get("toggle_ocr", "F10").upper()
            self.lbl_hint.setText(f"[{hk}]")
        except:
            pass

    def update_status(self, ocr_active: bool):
        self.update_shortcut_text()
        
        if ocr_active:
            self.lbl_ocr.setText("OCR: AÇIK")
            self.lbl_ocr.setStyleSheet("color: white; font-weight: bold; font-size: 9pt;")
            self.frame.setStyleSheet("""
                background-color: rgba(15, 15, 15, 230); 
                border: 1px solid #00FF96; 
                border-radius: 15px;
            """)
            self.lbl_jarvis.setStyleSheet("color: #00FF96; font-weight: 900; font-size: 10pt;")
        else:
            self.lbl_ocr.setText("OCR: KAPALI")
            self.lbl_ocr.setStyleSheet("color: #ff7675; font-weight: bold; font-size: 9pt;")
            self.frame.setStyleSheet("""
                background-color: rgba(15, 15, 15, 230); 
                border: 1px solid #ff7675; 
                border-radius: 15px;
            """)
            self.lbl_jarvis.setStyleSheet("color: #ff7675; font-weight: 900; font-size: 10pt;")


# ==========================================
# 3. HUD ARAYÜZÜ (SENİN "MÜKEMMEL ÇALIŞAN" KODUN - HİÇ DOKUNULMADI!)
# ==========================================

class OverlayHUD(QWidget):
    def __init__(self, image_cache):
        super().__init__()
        self.image_cache = image_cache
        self.current_img_url = "" 
        
        # Config Yükle
        self.hud_config = load_config().get("hud_region", {"top": 40, "left": -1, "width": 300, "height": 600})

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | 
                            Qt.WindowTransparentForInput | Qt.Tool | Qt.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Başlangıç Boyutu (Config'den)
        self.setFixedWidth(self.hud_config.get("width", 300))
        # Yükseklik içerik kadar uzayacak, ama maximum belirleyebiliriz
        self.setMaximumHeight(self.hud_config.get("height", 1000))

        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(5, 5, 5, 5)
        # self.layout.setSizeConstraint(QVBoxLayout.SetFixedSize) # İçeriğe göre uzasın ama genişlik sabit
        self.setLayout(self.layout)

        self.frame = QFrame(self)
        self.frame.setStyleSheet("background-color: rgba(15, 15, 15, 215); border: 2px solid rgba(0, 255, 150, 150); border-radius: 8px;")
        
        self.frame_layout = QVBoxLayout(self.frame)
        self.layout.addWidget(self.frame)

        self.title_label = QLabel()
        self.title_label.setAlignment(Qt.AlignCenter)
        self.frame_layout.addWidget(self.title_label)

        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.frame_layout.addWidget(self.image_label)
        
        self.badges_layout = FlowLayout()
        self.frame_layout.addLayout(self.badges_layout)
        
        # Danışman Tavsiyeleri
        self.advice_layout = QVBoxLayout()
        self.advice_layout.setSpacing(3)
        self.frame_layout.addLayout(self.advice_layout)
        
        self.grid_layout = QGridLayout()
        self.frame_layout.addLayout(self.grid_layout)

    def resizeEvent(self, event):
        # Konumlandırma (Config'e göre)
        screen = QApplication.desktop().screenGeometry()
        
        top = self.hud_config.get("top", 40)
        left = self.hud_config.get("left", -1)
        width = self.hud_config.get("width", 300)
        
        if left == -1:
            # Sağdan Hizala (Varsayılan)
            x = screen.width() - width - 20
        else:
            # Özel Konum
            x = left
            
        self.move(x, top)
        self.setFixedWidth(width)
        
        super().resizeEvent(event)

    def update_ui(self, vehicle_data):
        try:
            if not self.isVisible():
                self.show()
                # Geometry'i zorla güncelle (Config değişmiş olabilir)
                self.hud_config = load_config().get("hud_region", {"top": 40, "left": -1, "width": 300, "height": 600})
                self.resizeEvent(None)

            name = vehicle_data.get("Vehicle Name", "")
            v_class = vehicle_data.get("Vehicle Class", "")
            self.title_label.setText(f"<center><span style='font-size:16pt; color:{Theme.PRIMARY}; font-weight:bold;'>{name.upper()}</span><br><span style='font-size:12pt; color:{Theme.TEXT_SECONDARY};'>{v_class}</span></center>")
            self.image_label.clear()

            # Rozetleri Temizle
            for i in reversed(range(self.badges_layout.count())): 
                w = self.badges_layout.itemAt(i).widget()
                if w: w.deleteLater()

            # Yeni Rozetler
            for text, color in get_smart_badges(vehicle_data):
                b = QLabel(text)
                b.setFont(QFont("Segoe UI", 8, QFont.Bold))
                b.setStyleSheet(f"background-color: {color}; color: white; border-radius: 4px; padding: 3px 6px;")
                self.badges_layout.addWidget(b)

            # Resim İşlemleri
            img_url = vehicle_data.get("Image URL", "")
            self.current_img_url = img_url 
            if img_url in self.image_cache:
                self.set_image(img_url, self.image_cache[img_url])
            elif img_url and img_url != "Resim Bulunamadı":
                self.img_thread = ImageLoaderThread(img_url)
                self.img_thread.image_loaded_signal.connect(self.set_image)
                self.img_thread.start()

            # Danışman Tavsiyelerini Temizle + Yeniden Oluştur
            for i in reversed(range(self.advice_layout.count())):
                w = self.advice_layout.itemAt(i).widget()
                if w: w.deleteLater()

            if hasattr(self, 'db_data') and self.db_data:
                for text, color in get_vehicle_advice(vehicle_data, self.db_data):
                    adv = QLabel(f"  {text}")
                    adv.setFont(QFont("Segoe UI", 8))
                    adv.setStyleSheet(f"color: {color}; padding: 2px 4px;")
                    self.advice_layout.addWidget(adv)

            # Tabloyu Temizle
            for i in reversed(range(self.grid_layout.count())): 
                w = self.grid_layout.itemAt(i).widget()
                if w: w.deleteLater()

            row = 0
            exclude_exact = ["Vehicle Name", "Vehicle Class", "Link", "Image URL"]
            
            for key, value in vehicle_data.items():
                key_str = str(key)
                if "Variants" in key_str or "Liveries" in key_str:
                    continue

                if key_str not in exclude_exact and value and value != "Veri Yok":
                    lbl_title = QLabel(f"{key_str}:")
                    lbl_title.setFont(QFont("Segoe UI", 10, QFont.Bold)) 
                    lbl_title.setStyleSheet(f"color: {Theme.TEXT_SECONDARY};")
                    
                    # YENİ: ScrollingLabel Kullanımı (Kayan Yazı)
                    lbl_value = ScrollingLabel(str(value), color="#FFFFFF")
                    
                    self.grid_layout.addWidget(lbl_title, row, 0)
                    self.grid_layout.addWidget(lbl_value, row, 1)
                    row += 1
        except Exception as e:
            print(f"[HUD HATASI]: {e}")

    def set_image(self, url, qimage):
        """QImage'i QPixmap'e dönüştürüp gösterir (Ana thread'de çalışır)."""
        if qimage is None or qimage.isNull(): 
            return
        pixmap = QPixmap.fromImage(qimage)  # Ana thread'de dönüştür
        self.image_cache[url] = pixmap
        if self.current_img_url == url:
            self.image_label.setPixmap(pixmap.scaled(self.width() - 30, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def open_settings(self):
        if hasattr(self, 'settings_window'):
            self.settings_window.load_settings()
            self.settings_window.show()

# ==========================================
# 5. SNIPPER (İNTERAKTİF EKRAN SEÇİM ARACI)
# ==========================================
class InteractiveSnipper(QWidget):
    def __init__(self, initial_rect=None):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowState(Qt.WindowFullScreen)
        
        self.on_snip_callback = None
        self.on_close_callback = None # Kapanınca çağrılacak (iptal veya bitiş)
        
        self.start_pos = None
        self.current_pos = None
        self.setStyleSheet("background-color: black;")
        self.setWindowOpacity(0.4)  # Arka plan karartma
        
        # Tam ekran yap (Tüm monitörleri kapsa)
        self.geometry_rect = QApplication.desktop().geometry()
        self.setGeometry(self.geometry_rect)
        
        # Başlangıç bölgesi
        if initial_rect:
            self.selection = QRect(*initial_rect)
        else:
            # Varsayılan: Ekranın ortasında bir kutu
            cx, cy = self.width() // 2, self.height() // 2
            self.selection = QRect(cx - 200, cy - 100, 400, 200)

        self.on_snip_callback = None
        
        # Durum Değişkenleri
        self.dragging = False
        self.resizing = False
        self.resize_edge = None # 'TL', 'TR', 'BL', 'BR', 'T', 'B', 'L', 'R'
        self.drag_offset = QPoint()
        
        # Tutacak (Handle) Boyutu
        self.handle_size = 25 # Daha büyük tutacaklar
        self.setMouseTracking(True) # Hover efektleri için
        
        self.setup_control_panel()

    def setup_control_panel(self):
        self.control_panel = QFrame(self)
        self.control_panel.setStyleSheet("""
            QFrame {
                background-color: #2d3436;
                border: 2px solid #00FF96;
                border-radius: 15px;
            }
            QPushButton {
                font-family: 'Segoe UI', sans-serif;
                font-weight: bold;
                color: white;
                border-radius: 8px;
                padding: 10px 25px;
                font-size: 12pt;
            }
            QPushButton#confirm { background-color: #00FF96; color: #2d3436; }
            QPushButton#confirm:hover { background-color: #55efc4; }
            QPushButton#cancel { background-color: #d63031; }
            QPushButton#cancel:hover { background-color: #ff7675; }
        """)
        
        layout = QHBoxLayout(self.control_panel)
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(30)
        
        btn_confirm = QPushButton("✅ ONAYLA")
        btn_confirm.setObjectName("confirm")
        btn_confirm.setCursor(Qt.PointingHandCursor)
        btn_confirm.clicked.connect(self.finish_selection)
        
        btn_cancel = QPushButton("❌ İPTAL")
        btn_cancel.setObjectName("cancel")
        btn_cancel.setCursor(Qt.PointingHandCursor)
        btn_cancel.clicked.connect(self.close)
        
        layout.addWidget(btn_confirm)
        layout.addWidget(btn_cancel)
        
        self.control_panel.adjustSize()

    def resizeEvent(self, event):
        if hasattr(self, 'control_panel'):
            cp_width = self.control_panel.width()
            cp_height = self.control_panel.height()
            # Alt orta, biraz yukarıda
            self.control_panel.move(
                (self.width() - cp_width) // 2,
                self.height() - cp_height - 80 
            )
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 1. Arka Planı Karart (Seçili alan hariç)
        path = QPainterPath()
        path.addRect(0, 0, self.width(), self.height())
        
        # Seçili alanı çıkar (Highlight)
        if self.selection.isValid():
            path.addRect(QRectF(self.selection))
            
        painter.setBrush(QColor(0, 0, 0, 100)) # Yarı saydam siyah
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)
        
        # 2. Seçim Çerçevesi
        painter.setPen(QPen(QColor('#00FF96'), 5, Qt.DashLine)) # Daha kalın çizgi
        painter.setBrush(Qt.NoBrush)
        painter.drawRect(self.selection)
        
        # 3. Tutacakları Çiz (Handles)
        painter.setBrush(QColor('#00FF96'))
        painter.setPen(Qt.NoPen)
        for handle_rect in self.get_handles().values():
            painter.drawRect(handle_rect)
            
        # 4. Bilgi Metni (Sadece boyut bilgisi kalsın)
        txt = f"X: {self.selection.x()} Y: {self.selection.y()} W: {self.selection.width()} H: {self.selection.height()}"
        painter.setPen(QColor('white'))
        painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
        # Kutunun sol üstüne yaz
        painter.drawText(self.selection.x(), self.selection.y() - 10, txt)

    def get_handles(self):
        r = self.selection
        s = self.handle_size
        return {
            'TL': QRect(r.left() - s//2, r.top() - s//2, s, s),
            'TR': QRect(r.right() - s//2, r.top() - s//2, s, s),
            'BL': QRect(r.left() - s//2, r.bottom() - s//2, s, s),
            'BR': QRect(r.right() - s//2, r.bottom() - s//2, s, s),
        }

    def mousePressEvent(self, event):
        pos = event.pos()
        
        # 1. Tutacak Kontrolü
        handles = self.get_handles()
        for edge, rect in handles.items():
            if rect.contains(pos):
                self.resizing = True
                self.resize_edge = edge
                return

        # 2. Taşıma Kontrolü
        if self.selection.contains(pos):
            self.dragging = True
            self.drag_offset = pos - self.selection.topLeft()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        pos = event.pos()
        
        if self.dragging:
            new_pos = pos - self.drag_offset
            self.selection.moveTopLeft(new_pos)
            self.update()
            return
        
        if self.resizing:
            r = self.selection
            if self.resize_edge == 'TL': r.setTopLeft(pos)
            elif self.resize_edge == 'TR': r.setTopRight(pos)
            elif self.resize_edge == 'BL': r.setBottomLeft(pos)
            elif self.resize_edge == 'BR': r.setBottomRight(pos)
            self.selection = r.normalized()
            self.update()
            return

        # Cursor Güncelleme
        handles = self.get_handles()
        if handles['TL'].contains(pos) or handles['BR'].contains(pos):
            self.setCursor(Qt.SizeFDiagCursor)
        elif handles['TR'].contains(pos) or handles['BL'].contains(pos):
            self.setCursor(Qt.SizeBDiagCursor)
        elif self.selection.contains(pos):
            self.setCursor(Qt.OpenHandCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    def mouseReleaseEvent(self, event):
        self.dragging = False
        self.resizing = False
        self.setCursor(Qt.ArrowCursor)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Enter, Qt.Key_Return):
            self.finish_selection()
        elif event.key() == Qt.Key_Escape:
            self.close()

    def closeEvent(self, event):
        if self.on_close_callback:
            self.on_close_callback()
        super().closeEvent(event)

    def mouseDoubleClickEvent(self, event):
        if self.selection.contains(event.pos()):
            self.finish_selection()

    def finish_selection(self):
        if self.on_snip_callback:
            self.on_snip_callback(
                self.selection.x(), self.selection.y(),
                self.selection.width(), self.selection.height()
            )
        self.close()

# ==========================================
# 4. AYARLAR PENCERESİ
# ==========================================
class SettingsWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__()
        self.parent_window = parent
        self.setWindowTitle("Ayarlar")
        
        # 1. Ekran boyutlarını al
        screen = QApplication.primaryScreen().availableGeometry()
        
        # 2. Minimum ve maksimum boyutları hesapla
        min_width, min_height = 400, 500
        max_width = int(screen.width() * 0.9)
        max_height = int(screen.height() * 0.9)
        
        self.setMinimumSize(min_width, min_height)
        self.setMaximumSize(max_width, max_height)
        
        # 3. Kayıtlı geometriyi al veya varsayılanı kullan
        cfg = load_config()
        geom = cfg.get("ui_geometry", {}).get("SettingsWindow", {})
        
        # Varsayılan boyut
        default_width = min(600, int(screen.width() * 0.4))
        default_height = min(900, int(screen.height() * 0.8))
        
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
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        
        # Resizer'ı başlat
        self.resizer = FramelessResizer(self)
        
        # Modern Stil
        self.setStyleSheet("""
            QWidget { 
                font-family: 'Segoe UI', sans-serif; 
                background-color: #2d3436; 
                color: white; 
                font-size: 10pt;
            }
            QScrollBar:vertical { border: none; background: #2d3436; width: 8px; border-radius: 4px; }
            QLabel {
                font-weight: bold;
                color: #dfe6e9;
            }
            QLineEdit, QSpinBox {
                background-color: #636e72;
                border: 1px solid #b2bec3;
                border-radius: 4px;
                padding: 5px;
                color: white;
                font-weight: bold;
            }
            QPushButton {
                background-color: #0984e3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #74b9ff;
            }
            QGroupBox {
                border: 2px solid #b2bec3;
                border-radius: 6px;
                margin-top: 20px;
                font-weight: bold;
                color: #00FF96;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 5px;
                left: 10px;
            }
            QMessageBox {
                background-color: #2d3436;
                color: white;
            }
            QMessageBox QLabel {
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #0984e3;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 15px;
            }
        """)


        
        # 1. Kayıtlı Geometriyi Al veya Varsayılanı Hesapla
        cfg = load_config()
        geom = cfg.get("ui_geometry", {}).get("SettingsWindow", {})
        
        width_s = geom.get("width", 600)
        height_s = geom.get("height", 900)
        
        screen = QApplication.primaryScreen().availableGeometry()
        
        # Ekran yüksekliğinden büyükse sığdır
        if height_s > screen.height() - 40:
             height_s = screen.height() - 40

        self.setMinimumSize(400, 500)
        self.resize(width_s, height_s)

        if geom.get("x", -1) != -1:
            self.move(geom["x"], geom["y"])
        else:
            left = screen.x() + (screen.width() - width_s) // 2
            top = screen.y() + (screen.height() - height_s) // 2
            self.move(left, top)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        self.setLayout(main_layout)
        
        # Başlık
        title = QLabel("⚙️ AYARLAR")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16pt; font-weight: bold; color: #00FF96;")
        main_layout.addWidget(title)
        
        # Scroll Area (Artık sığmayabilir)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")
        content_widget = QWidget()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)

        # --- GENEL AYARLAR (QGroupBox) ---
        general_group = QGroupBox("Genel Ayarlar")
        general_layout = QFormLayout()
        general_layout.setSpacing(10)
        general_layout.setLabelAlignment(Qt.AlignLeft)
        
        # OCR Motor Bilgisi
        from workers import OCR_ENGINE
        if OCR_ENGINE == "winocr":
            ocr_info = QLabel("✅ Windows OCR (yerleşik)")
            ocr_info.setStyleSheet("color: #00FF96; font-weight: bold;")
        else:
            ocr_info = QLabel("⚙️ Tesseract OCR")
            ocr_info.setStyleSheet("color: #f0ad4e; font-weight: bold;")
        general_layout.addRow("OCR Motoru:", ocr_info)
        
        # Kısayollar
        self.hk_gallery = QLineEdit()
        self.hk_gallery.setPlaceholderText("Örn: f11")
        general_layout.addRow("Galeri Tuşu:", self.hk_gallery)
        
        self.hk_ownership = QLineEdit()
        self.hk_ownership.setPlaceholderText("Örn: f9")
        general_layout.addRow("Garaj Tuşu:", self.hk_ownership)

        self.hk_ocr = QLineEdit()
        self.hk_ocr.setPlaceholderText("Örn: f10")
        general_layout.addRow("OCR Aç/Kapa:", self.hk_ocr)
        
        general_group.setLayout(general_layout)
        content_layout.addWidget(general_group)
        
        # --- OCR AYARLARI (QGroupBox) ---
        ocr_group = QGroupBox("OCR Tarama Bölgesi (SOL ÜST)")
        ocr_layout = QFormLayout() 
        ocr_layout.setSpacing(10)
        
        # Bölge Seç Butonu
        self.snip_btn = QPushButton("🖱️ OCR ALANI SEÇ")
        self.snip_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.snip_btn.setStyleSheet("background: #e17055; color: white;")
        self.snip_btn.clicked.connect(self.start_snip)
        ocr_layout.addRow(self.snip_btn)
        
        # Koordinatlar
        self.ocr_left = QSpinBox(); self.ocr_left.setRange(0, 5000)
        ocr_layout.addRow("Sol (X):", self.ocr_left)
        
        self.ocr_top = QSpinBox(); self.ocr_top.setRange(0, 5000)
        ocr_layout.addRow("Üst (Y):", self.ocr_top)
        
        self.ocr_width = QSpinBox(); self.ocr_width.setRange(50, 5000)
        ocr_layout.addRow("Genişlik:", self.ocr_width)
        
        self.ocr_height = QSpinBox(); self.ocr_height.setRange(10, 2000)
        ocr_layout.addRow("Yükseklik:", self.ocr_height)
        
        ocr_group.setLayout(ocr_layout)
        content_layout.addWidget(ocr_group)

        # --- HUD AYARLARI (QGroupBox) ---
        hud_group = QGroupBox("HUD Bilgi Penceresi (SAĞ ÜST)")
        hud_layout = QFormLayout()
        hud_layout.setSpacing(10)

        # HUD Seç Butonu
        self.hud_snip_btn = QPushButton("🖱️ HUD KONUMU SEÇ")
        self.hud_snip_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self.hud_snip_btn.setStyleSheet("background: #0984e3; color: white;")
        self.hud_snip_btn.clicked.connect(self.start_hud_snip)
        hud_layout.addRow(self.hud_snip_btn)

        # Koordinatlar
        self.hud_left = QSpinBox(); self.hud_left.setRange(-1, 5000) # -1: Otomatik Sağ
        self.hud_left.setSpecialValueText("Oto (Sağ)")
        hud_layout.addRow("Sol (X):", self.hud_left)

        self.hud_top = QSpinBox(); self.hud_top.setRange(0, 5000)
        hud_layout.addRow("Üst (Y):", self.hud_top)
        
        self.hud_width = QSpinBox(); self.hud_width.setRange(50, 5000)
        hud_layout.addRow("Genişlik:", self.hud_width)
        
        self.hud_height = QSpinBox(); self.hud_height.setRange(10, 2000)
        hud_layout.addRow("Max Yükseklik:", self.hud_height) 

        hud_group.setLayout(hud_layout)
        content_layout.addWidget(hud_group)
        
        # --- BUTONLAR ---
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(15)
        
        save_btn = QPushButton("KAYDET")
        save_btn.setCursor(QCursor(Qt.PointingHandCursor))
        save_btn.setStyleSheet("background: #00FF96; color: #2d3436; font-weight: bold; padding: 10px; font-size: 11pt;")
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("İPTAL")
        cancel_btn.setCursor(QCursor(Qt.PointingHandCursor))
        cancel_btn.setStyleSheet("background: #d63031; color: white; font-weight: bold; padding: 10px; font-size: 11pt;")
        cancel_btn.clicked.connect(self.close)
        btn_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(btn_layout)
        
        self.info_label = QLabel("Ayarlar kaydedildikten sonra yeniden başlatma gerekir.")
        self.info_label.setStyleSheet("color: #b2bec3; font-size: 9pt; margin-top: 5px;")
        self.info_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.info_label)
        
        self.load_settings()

    def mousePressEvent(self, event):
        self.resizer.handle_mouse_press(event)

    def mouseMoveEvent(self, event):
        self.resizer.handle_mouse_move(event)

    def mouseReleaseEvent(self, event):
        self.resizer.handle_mouse_release(event)

    def closeEvent(self, event):
        """Pencere kapandığında boyut ve konumu kaydet."""
        self._save_geometry()
        if self.parent_window:
            self.parent_window.show()
        super().closeEvent(event)
    
    def hideEvent(self, event):
        """Pencere gizlendiğinde de boyut ve konumu kaydet."""
        self._save_geometry()
        super().hideEvent(event)
    
    def _save_geometry(self):
        """Pencere geometrisini config'e kaydet."""
        cfg = load_config()
        if "ui_geometry" not in cfg: 
            cfg["ui_geometry"] = {}
        
        geom = self.geometry()
        cfg["ui_geometry"]["SettingsWindow"] = {
            "width": geom.width(),
            "height": geom.height(),
            "x": geom.x(),
            "y": geom.y()
        }
        save_config(cfg)



    def load_settings(self):
        cfg = load_config()

        
        hotkeys = cfg.get("hotkeys", {})
        self.hk_gallery.setText(hotkeys.get("toggle_gallery", "f11"))
        self.hk_ownership.setText(hotkeys.get("toggle_ownership", "f9"))
        self.hk_ocr.setText(hotkeys.get("toggle_ocr", "f10"))
        
        ocr = cfg.get("ocr_region", {})
        self.ocr_top.setValue(ocr.get("top", 0))
        self.ocr_left.setValue(ocr.get("left", 0))
        self.ocr_width.setValue(ocr.get("width", 500))
        self.ocr_height.setValue(ocr.get("height", 800))

        hud = cfg.get("hud_region", {})
        self.hud_top.setValue(hud.get("top", 40))
        self.hud_left.setValue(hud.get("left", -1))
        self.hud_width.setValue(hud.get("width", 300))
        self.hud_height.setValue(hud.get("height", 600))

    def save_settings(self):
        cfg = load_config()

        
        cfg["hotkeys"]["toggle_gallery"] = self.hk_gallery.text()
        cfg["hotkeys"]["toggle_ownership"] = self.hk_ownership.text()
        cfg["hotkeys"]["toggle_ocr"] = self.hk_ocr.text()
        
        cfg["ocr_region"]["top"] = self.ocr_top.value()
        cfg["ocr_region"]["left"] = self.ocr_left.value()
        cfg["ocr_region"]["width"] = self.ocr_width.value()
        cfg["ocr_region"]["height"] = self.ocr_height.value()

        if "hud_region" not in cfg: cfg["hud_region"] = {}
        cfg["hud_region"]["top"] = self.hud_top.value()
        cfg["hud_region"]["left"] = self.hud_left.value()
        cfg["hud_region"]["width"] = self.hud_width.value()
        cfg["hud_region"]["height"] = self.hud_height.value()
        
        save_config(cfg)
        QMessageBox.information(self, "Kaydedildi", "Ayarlar başarıyla kaydedildi.\nDeğişikliklerin tam olarak etki etmesi için lütfen uygulamayı yeniden başlatın.")
        self.close()

    def start_snip(self):
        self.hide()
        x = self.ocr_left.value()
        y = self.ocr_top.value()
        w = self.ocr_width.value()
        h = self.ocr_height.value()
        
        initial_rect = (x, y, w, h) if w > 0 and h > 0 else None
        
        self.snipper = InteractiveSnipper(initial_rect)
        self.snipper.on_snip_callback = self.on_snip_finished
        self.snipper.on_close_callback = self.show
        self.snipper.show()

    def on_snip_finished(self, x, y, w, h):
        self.ocr_left.setValue(x)
        self.ocr_top.setValue(y)
        self.ocr_width.setValue(w)
        self.ocr_height.setValue(h)
        self.show()

    def start_hud_snip(self):
        self.hide()
        x = self.hud_left.value()
        y = self.hud_top.value()
        w = self.hud_width.value()
        h = self.hud_height.value()
        
        # Eğer -1 ise (Sağdaysa) varsayılan bir yer aç
        if x == -1:
            screen = QApplication.desktop().screenGeometry()
            x = screen.width() - w - 20
            
        initial_rect = (x, y, w, h) if w > 0 and h > 0 else None
        
        # HUD Snipper'ı biraz farklı olabilir (Belki renk?) ama aynı sınıfı kullanabiliriz
        self.hud_snipper = InteractiveSnipper(initial_rect)
        self.hud_snipper.on_snip_callback = self.on_hud_snip_finished
        self.hud_snipper.on_close_callback = self.show
        self.hud_snipper.show()

    def on_hud_snip_finished(self, x, y, w, h):
        self.hud_left.setValue(x)
        self.hud_top.setValue(y)
        self.hud_width.setValue(w)
        self.hud_height.setValue(h)
        self.show()
        
