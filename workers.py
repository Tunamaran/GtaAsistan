# workers.py
"""Arka plan işçi thread'leri: OCR, kısayol ve resim yükleme."""
import time
import re
import asyncio
import logging
from typing import Dict, List, Optional, Tuple

import requests
import numpy as np
import cv2
import mss
import keyboard
from thefuzz import process, fuzz
from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage

from config import load_config

# Config yükle
cfg = load_config()

# === OCR Motor Seçimi ===
LCD = None  # Lazy Loaded
OCR_ENGINE = None

def get_ocr_engine():
    global OCR_ENGINE
    if OCR_ENGINE is not None:
        return OCR_ENGINE
    
    logging.info("OCR Motoru başlatılıyor...")
    try:
        import winocr
        from PIL import Image as PILImage
        
        # Testi burada yap, import anında değil
        try:
            _test_loop = asyncio.new_event_loop()
            _test_img = PILImage.new('L', (50, 20), 255)
            _test_loop.run_until_complete(winocr.recognize_pil(_test_img, lang='en'))
            _test_loop.close()
            OCR_ENGINE = "winocr"
            logging.info("[OCR] Windows OCR motoru aktif (hızlı mod)")
            print("[OCR] [OK] Windows OCR motoru aktif (hızlı mod)")
        except Exception as e:
            logging.warning(f"[OCR] Windows OCR testi başarısız: {e}")
            raise e

    except (ImportError, RuntimeError, OSError, AttributeError, AssertionError) as e:
        logging.warning(f"[OCR] Windows OCR kullanılamıyor, Tesseract aranıyor... Hata: {e}")
        print("[OCR] [UYARI] Windows OCR yüklenemedi, Tesseract kullanılıyor.")
        
        try:
            import pytesseract
            _tess_path = cfg.get("tesseract_path", r'C:\Program Files\Tesseract-OCR\tesseract.exe')
            pytesseract.pytesseract.tesseract_cmd = _tess_path
            OCR_ENGINE = "tesseract"
            logging.info("[OCR] Tesseract OCR kullanılıyor.")
            print("[OCR] [BILGI] Tesseract OCR kullanılıyor.")
        except ImportError:
             logging.error("Hiçbir OCR motoru bulunamadı!")
             OCR_ENGINE = "none" # Fail gracefully
    
    return OCR_ENGINE


class HotkeyThread(QThread):
    """Klavye kısayollarını dinleyen thread."""
    toggle_gallery_signal = pyqtSignal()
    toggle_ownership_signal = pyqtSignal()
    toggle_ocr_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.running = True

    def run(self) -> None:
        hk_gallery = cfg["hotkeys"].get("toggle_gallery", "f11")
        keyboard.add_hotkey(hk_gallery, lambda: self.toggle_gallery_signal.emit())
        
        hk_ownership = cfg["hotkeys"].get("toggle_ownership", "f9")
        keyboard.add_hotkey(hk_ownership, lambda: self.toggle_ownership_signal.emit())

        hk_ocr = cfg["hotkeys"].get("toggle_ocr", "f10")
        keyboard.add_hotkey(hk_ocr, lambda: self.toggle_ocr_signal.emit())
        
        # Bloklayıcı wait yerine loop kullan
        while self.running:
            time.sleep(0.1)
        
        # Cleanup
        keyboard.unhook_all()

    def stop(self):
        """Thread'i durdur."""
        self.running = False


class ImageLoaderThread(QThread):
    """URL'den resim indiren thread."""
    image_loaded_signal = pyqtSignal(str, QImage)  # QPixmap yerine QImage
    
    def __init__(self, url: str):
        super().__init__()
        self.url = url
    
    def run(self) -> None:
        try:
            if self.url and self.url.startswith("http"):
                headers = {"User-Agent": "Mozilla/5.0"}
                resp = requests.get(self.url, headers=headers, timeout=5)
                if resp.status_code == 200:
                    img = QImage()
                    img.loadFromData(resp.content)
                    if not img.isNull():
                        self.image_loaded_signal.emit(self.url, img)  # QImage gönder
        except Exception as e:
            print(f"[UYARI] Resim yükleme hatası: {e}")


class OcrThread(QThread):
    """Ekrandaki araç isimlerini OCR ile okuyan thread."""
    vehicle_found_signal = pyqtSignal(dict)
    hide_hud_signal = pyqtSignal() 
    gta_window_active_signal = pyqtSignal(bool) # YENİ: Pencere odak durumu
    
    # OCR sonuçlarını filtreleyen kara liste
    BLACKLIST = [
        "garage", "request", "delivery", "return", "mechanic",
        "apartment", "suite", "facility", "arcade", "nightclub",
        "bunker", "empty", "property", "boss", "health", "ammo",
        "clubhouse", "office", "arena", "casino", "penthouse",
        "auto shop", "agency", "eclipse", "hawick", "blvd", "free",
        "select", "manage", "transporter", "storage", "organization",
        "call", "personal", "vehicle", "special", "mansions",
        "garment", "factory", "bail", "reservoir", "land act"
    ]
    
    # ... (existing code) ...


    
    # Görüntü İşleme Sabitleri (Tesseract kontur modu)
    MIN_CONTOUR_WIDTH = 200
    MAX_CONTOUR_WIDTH = 650
    MIN_CONTOUR_HEIGHT = 35
    MAX_CONTOUR_HEIGHT = 85
    BRIGHTNESS_THRESHOLD = 80
    BINARY_THRESHOLD = 140
    MATCH_THRESHOLD = 85
    HUD_TIMEOUT = 1.5  # saniye
    
    def __init__(self, search_dict: Dict[str, dict]):
        super().__init__()
        self.search_dict = search_dict
        self.search_keys = list(search_dict.keys())
        self.running = True
        self.paused = False  # YENİ: Duraklatma kontrolü
        self.last_gta_state = None
        self._loop = None

    # =====================================================
    # Tesseract modu: Kontur tabanlı (eski yaklaşım)
    # =====================================================
    def _preprocess_roi(self, roi: np.ndarray) -> Optional[np.ndarray]:
        """ROI'yi OCR için ön işler. Karanlık zemini atlar."""
        roi_enlarged = cv2.resize(roi, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
        roi_blurred = cv2.GaussianBlur(roi_enlarged, (3, 3), 0)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        roi_contrasted = clahe.apply(roi_blurred)
        
        if np.mean(roi_contrasted) <= self.BRIGHTNESS_THRESHOLD:
            return None
        
        _, roi_final = cv2.threshold(roi_contrasted, self.BINARY_THRESHOLD, 255, cv2.THRESH_BINARY)
        roi_padded = cv2.copyMakeBorder(roi_final, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[255, 255, 255])
        return roi_padded

    def _extract_text_tesseract(self, roi_padded: np.ndarray) -> Optional[str]:
        """Tesseract ile metin okur."""
        try:
            return pytesseract.image_to_string(roi_padded, config='--oem 3 --psm 7').strip()
        except Exception:
            return None

    # =====================================================
    # Metin temizleme & eşleştirme (her iki mod için ortak)
    # =====================================================
    def _clean_text(self, raw_text: str) -> Optional[str]:
        """Ham OCR metnini temizler ve filtreler."""
        if not raw_text or len(raw_text.strip()) < 3:
            return None
        
        text = raw_text.strip()
        
        # Regex: "Request Personal Aircraft < Cargobob >" -> "Cargobob"
        bracket_match = re.search(r'<(.+?)>', text)
        if bracket_match:
            clean = bracket_match.group(1).strip()
            return clean if len(clean) >= 3 else None
        
        # Temizlik
        clean = text.replace('<', '').replace('>', '').replace('|', '')
        clean = clean.replace('_', '').replace('«', '').replace('»', '').strip()
        
        if len(clean) < 3:
            return None
        if any(b in clean.lower() for b in self.BLACKLIST):
            return None
        if not re.search(r'[a-zA-Z0-9]', clean):
            return None
            
        # Dosya uzantılarını ele (örn. main.py, setup.exe)
        if re.search(r'\.[a-zA-Z]{2,4}$', clean):
            return None
        
        return clean

    def _match_vehicle(self, clean_text: str) -> Optional[Tuple[str, int]]:
        """Metni veritabanıyla eşleştirir (Çok aşamalı filtreleme)."""
        # 1. Geniş kapsamlı arama (WRatio) - İlk 10 adayı al
        # Eşik değeri düşük tutuyoruz ki "RM-IO" gibi hatalı okumaları yakalayalım
        candidates = process.extract(clean_text, self.search_keys, scorer=fuzz.WRatio, limit=10)
        
        # 2. Çok kötü eşleşmeleri ele (WRatio < 60)
        valid_candidates = [c for c in candidates if c[1] >= 60]
        if not valid_candidates:
            return None
        
        # 3. Gelişmiş Skorlama (TokenSet, TokenSort)
        scored_candidates = []
        for match_text, w_score in valid_candidates:
            # TokenSet: Kelime kümesi eşleşmesi (Marka ismi eksikse bile 100 verir)
            # TokenSort: Kelime sıralaması ve fazlalık cezası (Tam eşleşme ayrımı için)
            set_ratio = fuzz.token_set_ratio(clean_text, match_text)
            sort_ratio = fuzz.token_sort_ratio(clean_text, match_text)
            
            scored_candidates.append((match_text, w_score, set_ratio, sort_ratio))
        
        # 4. Sıralama Stratejisi:
        # Öncelik 1: TokenSet (Alakasız alt dizeleri eler - örn. 'Bus' vs 'Bombushka')
        # Öncelik 2: TokenSort (Tam eşleşmeyi bulur - örn. 'Dubsta' vs 'Dubsta 6x6')
        # Öncelik 3: WRatio (Genel benzerlik)
        scored_candidates.sort(key=lambda x: (x[2], x[3], x[1]), reverse=True)
        
        best = scored_candidates[0]
        best_match, w_score, set_ratio, sort_ratio = best
        
        # 5. Son Karar Eşiği
        # TokenSet oranı çok düşükse reddet (örn. 'Bus' vs 'RM-IO Bombushka' -> Set=33 -> RED)
        # Ancak "RM-IO" vs "RM-10" -> Set=89 -> KABUL
        # "Mansions" vs "Omnis" -> Set=62 -> RED (Eşik 85 yapıldı - Kullanıcı isteği)
        if set_ratio < 85:
            # print(f"[RED] {clean_text} -> {best_match} (Set: {set_ratio})")
            return None
            
        # Debug
        # print(f"[MATCH] {clean_text} -> {best_match} (W:{w_score}, Set:{set_ratio}, Sort:{sort_ratio})")
        
        # Skoru WRatio olarak döndür (uyumluluk için) veya ortalama al
        return best_match, w_score

    # =====================================================
    # Windows OCR modu: Tüm ekran taraması (kontur yok)
    # =====================================================
    def _run_winocr(self, gray: np.ndarray):  # -> List[OcrLine]
        """Windows OCR ile tüm ekranı tarar, satır nesnelerini döndürür."""
        import winocr # Fonksiyon içinde import ederek global scope karmaşasından kaçınalım
        from PIL import Image as PILImage
        try:
            pil_img = PILImage.fromarray(gray)
            result = self._loop.run_until_complete(
                winocr.recognize_pil(pil_img, lang="en")
            )
            return result.lines
        except Exception:
            return []

    # =====================================================
    # Ana döngü
    # =====================================================
    def run(self) -> None:
        """Ana OCR döngüsü — motor tipine göre farklı yol izler."""
        engine = get_ocr_engine()
        if engine == "winocr":
            self._run_winocr_loop()
        elif engine == "tesseract":
            self._run_tesseract_loop()
        else:
            logging.error("OCR Motoru başlatılamadığı için thread duruyor.")

    def _is_gta_active(self) -> bool:
        """Aktif pencerenin GTA 5 olup olmadığını kontrol eder."""
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return False
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            return "Grand Theft Auto V" in buff.value
        except Exception:
            return True  # Hata durumunda devam et

    def _run_winocr_loop(self) -> None:
        """Windows OCR döngüsü: Tüm ekranı tarar, EN PARLAK (seçili) satırı bulur."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        monitor = cfg.get("ocr_region", {"top": 0, "left": 0, "width": 500, "height": 800})
        last_matched = ""
        last_seen = time.time()
        
        self.no_vehicle_counter = 0

        with mss.mss() as sct:  # Context manager
            try:
                while self.running:
                    # Önce pencere kontrolü
                    is_gta = self._is_gta_active()
                    if is_gta != self.last_gta_state:
                        self.last_gta_state = is_gta
                        self.gta_window_active_signal.emit(is_gta)
                        logging.debug(f"[DEBUG] GTA Penceresi Aktif: {is_gta}")
                    
                    if not is_gta:
                        self.hide_hud_signal.emit()
                        time.sleep(1)
                        continue

                    # Duraklatma kontrolü
                    if self.paused:
                        self.hide_hud_signal.emit()
                        time.sleep(1)
                        continue

                    try:
                        # 1. Ekranı yakala
                        screen_grab = np.array(sct.grab(monitor))
                        gray = cv2.cvtColor(screen_grab, cv2.COLOR_BGRA2GRAY)
                        # İYİLEŞTİRME: Resmi 2x büyüt (Küçük metinleri okumak için - örn. Dubsta 6x6)
                        h_orig, w_orig = gray.shape
                        gray_2x = cv2.resize(gray, (w_orig*2, h_orig*2), interpolation=cv2.INTER_LINEAR)
                        
                        # 2. Windows OCR ile tüm satırları oku (Büyütülmüş resim ile)
                        # 2. Windows OCR ile tüm satırları oku (Büyütülmüş resim ile)
                        lines = self._run_winocr(gray_2x)
                        logging.debug(f"[DEBUG] Bulunan satır sayısı: {len(lines)}")
                        
                        candidates = []  # (araç_ismi, skor, parlaklık, ham_metin)
                        
                        for line_idx, line in enumerate(lines):
                            raw_text = line.text.strip()
                            if raw_text:
                                logging.debug(f"[DEBUG] Satır {line_idx}: '{raw_text}'")
                            
                            # 3. Temizle
                            clean = self._clean_text(raw_text)
                            if not clean:
                                logging.debug(f"[DEBUG] Temizleme sonrası boş: '{raw_text}'")
                                continue
                            
                            logging.debug(f"[DEBUG] Temiz metin: '{clean}'")
                            
                            # 4. Eşleştir
                            match_result = self._match_vehicle(clean)
                            if match_result:
                                match, score = match_result
                                
                                # 5. Parlaklık Hesapla (Highlight tespiti için)
                                # Koordinatlar 2x büyütülmüş resme göredir
                                words = list(line.words)
                                if words:
                                    w_first = words[0].bounding_rect
                                    w_last = words[-1].bounding_rect
                                    
                                    x = int(w_first.x)
                                    y = int(w_first.y)
                                    w = int(w_last.x + w_last.width - w_first.x)
                                    h = int(max(w_first.height, w_last.height))
                                    
                                    # Güvenlik kontrolü (gray_2x boyutlarına göre)
                                    y1 = max(0, y)
                                    y2 = min(gray_2x.shape[0], y + h)
                                    x1 = max(0, x)
                                    x2 = min(gray_2x.shape[1], x + w)
                                    
                                    if x2 > x1 and y2 > y1:
                                        roi = gray_2x[y1:y2, x1:x2]
                                        brightness = float(np.mean(roi))
                                        candidates.append((match, score, brightness, clean))
                        
                        # 6. En parlak (highlight olan) adayı seç
                        # YENİ: Sadece parlak (seçili) öğeleri dikkate al (Başlıkları ve seçili olmayanları eler)
                        logging.debug(f"[DEBUG] Adaylar (Filtre Öncesi): {[(c[3], int(c[2])) for c in candidates]}")
                        candidates = [c for c in candidates if c[2] >= 100]
                        if not candidates:
                             logging.debug("[DEBUG] Parlaklık filtresinden geçen aday yok.")
                        
                        if candidates:
                            # Parlaklığa göre sırala (en yüksek en başa)
                            candidates.sort(key=lambda x: x[2], reverse=True)
                            
                            best_match, best_score, best_br, best_clean = candidates[0]
                            
                            # Debug
                            # print(f"[OCR] Adaylar: {[(c[3], int(c[2])) for c in candidates]}")
                            
                            detected = True
                            last_seen = time.time()
                            
                            if best_match != last_matched:
                                last_matched = best_match
                                print(f"[OCR SEÇİLDİ] {best_clean} -> {best_match} (Skor: {best_score}, Parlaklık: {best_br:.1f})")
                                self.vehicle_found_signal.emit(self.search_dict[best_match])
                        
                        # Araç kaybolursa HUD'ı gizle
                        if not candidates and last_matched != "" and (time.time() - last_seen > self.HUD_TIMEOUT):
                            self.hide_hud_signal.emit()
                            last_matched = ""
                    
                    except Exception as e:
                        print(f"[HATA] OCR Döngüsü Hatası: {e}")
                        self.hide_hud_signal.emit()
                        last_matched = ""
                        time.sleep(1)
                    
                    time.sleep(0.2)  # Seri tepki için düşük gecikme
            finally:
                if self._loop:
                    self._loop.close()

    def _run_tesseract_loop(self) -> None:
        """Tesseract döngüsü: Kontur tabanlı, ROI bazlı OCR."""
        monitor = cfg.get("ocr_region", {"top": 0, "left": 0, "width": 500, "height": 800})
        last_matched = ""
        last_seen = time.time()

        with mss.mss() as sct:  # Context manager
            try:
                while self.running:
                    # Pencere Kontrolü (Tesseract Modu İçin Ekledim)
                    is_gta = self._is_gta_active()
                    if is_gta != self.last_gta_state:
                        self.last_gta_state = is_gta
                        self.gta_window_active_signal.emit(is_gta)
                    
                    if not is_gta:
                        self.hide_hud_signal.emit()
                        time.sleep(1)
                        continue

                    if self.paused:
                        self.hide_hud_signal.emit()
                        time.sleep(1)
                        continue

                    try:
                        screen_grab = np.array(sct.grab(monitor))
                        gray = cv2.cvtColor(screen_grab, cv2.COLOR_BGRA2GRAY)
                        
                        _, mask = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY)
                        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        detected = False
                        
                        for cnt in contours:
                            x, y, w, h = cv2.boundingRect(cnt)
                            if not (self.MIN_CONTOUR_WIDTH < w < self.MAX_CONTOUR_WIDTH 
                                    and self.MIN_CONTOUR_HEIGHT < h < self.MAX_CONTOUR_HEIGHT):
                                continue
                            
                            crop_w = w - 10 if w > 50 else w
                            roi = gray[y:y+h, x:x+crop_w]
                            
                            roi_padded = self._preprocess_roi(roi)
                            if roi_padded is None:
                                continue
                            
                            raw_text = self._extract_text_tesseract(roi_padded)
                            clean = self._clean_text(raw_text) if raw_text else None
                            if not clean:
                                continue
                            
                            match_result = self._match_vehicle(clean)
                            if match_result:
                                match, score = match_result
                                detected = True
                                last_seen = time.time()
                                
                                if match != last_matched:
                                    last_matched = match
                                    print(f"[OCR BULUNDU] {clean} -> {match} (Skor: {score})")
                                    self.vehicle_found_signal.emit(self.search_dict[match])
                        
                        if not detected and last_matched != "" and (time.time() - last_seen > self.HUD_TIMEOUT):
                            self.hide_hud_signal.emit() 
                            last_matched = ""
                    
                    except Exception as e:
                        print(f"[HATA] OCR Döngüsü Hatası: {e}")
                        self.hide_hud_signal.emit()
                        last_matched = ""
                        time.sleep(1)
                    
                    time.sleep(0.5)
            finally:
                # Cleanup
                self.hide_hud_signal.emit()