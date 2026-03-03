# workers.py
"""Arka plan işçi thread'leri: OCR, kısayol ve resim yükleme."""
import time
import re
import os
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
import i18n
from config import load_config, _get_default_tesseract_path

# Config yükle
cfg = load_config()

# === OCR Motor Seçimi ===
pytesseract = None
LCD = None  # Lazy Loaded
OCR_ENGINE = None

def get_ocr_engine():
    global OCR_ENGINE
    if OCR_ENGINE is not None:
        return OCR_ENGINE
    
    logging.info(i18n.t("workers.ocr_initializing"))
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
            logging.info(i18n.t("workers.winocr_active"))
            print(f"[OCR] [OK] {i18n.t('workers.winocr_active')}")
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logging.warning(f"[OCR] Windows OCR init failed. Details:\n{error_details}")
            # Hata mesajını daha anlaşılır hale getir (Kullanıcıya göstermek için saklanabilir)
            raise e

    except Exception as e:
        logging.warning(f"{i18n.t('workers.winocr_fail_fallback')} {e}")
        print(f"[OCR] [UYARI] {i18n.t('workers.winocr_fail_fallback')}")
        
        try:
            global pytesseract
            import pytesseract
            # Dinamik yol kontrolü
            _tess_path = cfg.get("tesseract_path", _get_default_tesseract_path())

            if not os.path.exists(_tess_path):
                logging.error(f"{i18n.t('workers.tesseract_not_found')}: {_tess_path}")
                _tess_path = _get_default_tesseract_path()
                
            pytesseract.pytesseract.tesseract_cmd = _tess_path
            OCR_ENGINE = "tesseract"
            logging.info(f"{i18n.t('workers.tesseract_active')} {_tess_path}")
            print(f"[OCR] [BILGI] {i18n.t('workers.tesseract_active')} ({_tess_path})")
        except Exception as te:
             logging.error(f"Tesseract yapılandırılamadı: {te}")
             OCR_ENGINE = "none"
    
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
        except Exception:
            logging.exception("[ImageLoaderThread] Resim yükleme hatası")


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
        self.paused = False
        self.last_gta_state = None
        self._loop = None
        
        # Ekran Çözünürlüğüne Göre Ölçek Faktörü (Tesseract Konturları İçin)
        from config import get_screen_resolution, BASELINE_RESOLUTION
        curr_w, curr_h = get_screen_resolution()
        self.scale_factor = curr_h / BASELINE_RESOLUTION[1]
        logging.debug(f"[OCR] Ölçek faktörü belirlendi: {self.scale_factor:.2f} ({curr_h}/1600)")

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
        
        # 3. Gelişmiş Skorlama
        scored_candidates = []
        for match_text, w_score in valid_candidates:
            # TokenSet: Kelime kümesi alt-küme ise (örn "Vigero" içinde "Vigero ZX" yok ama tersi var)
            set_ratio = fuzz.token_set_ratio(clean_text, match_text)
            # TokenSort: Tüm kelimeler aynı mı (Uzunluk farkını cezalandırır)
            sort_ratio = fuzz.token_sort_ratio(clean_text, match_text)
            # Ratio: Tam bir Levenshtein mesafesi (Harfi harfine aynılık)
            exact_ratio = fuzz.ratio(clean_text, match_text)
            
            scored_candidates.append((match_text, w_score, set_ratio, sort_ratio, exact_ratio))
        
        # 4. Sıralama Stratejisi (DÜZELTİLDİ):
        # Önceki sürümde TokenSet 1. sıradaydı. Bu durum "Vigero ZX Convertible" araması yapıldığında
        # veritabanındaki "Vigero" kelimesi ile TokenSet=100 çıkarıyordu çünkü "Vigero" kelimesi aranan metnin tam alt kümesiydi.
        # ÇÖZÜM: Öncelik 1'e EXACT RATIO (Birebir eşleşme) veya TOKEN SORT koyuyoruz.
        # Sıralama Önceliği: 
        # 1. exact_ratio (Birebir eşleşmeye en yakın olan, harf sayısı tutan)
        # 2. sort_ratio (Aynı kelimeleri içeren ama sırası karışık olan)
        # 3. set_ratio (Eksik kelimesi olan ama alakasız olmayan)
        scored_candidates.sort(key=lambda x: (x[4], x[3], x[2], x[1]), reverse=True)
        
        best = scored_candidates[0]
        best_match, w_score, set_ratio, sort_ratio, exact_ratio = best
        
        # 5. Son Karar Eşiği
        # TokenSet veya Exact Ratio çok düşükse reddet
        if set_ratio < 85 and exact_ratio < 70:
            return None
            
        # Skor olarak güvenilir bir ortalama döndür
        final_score = (exact_ratio + sort_ratio) // 2
        if final_score < 50:
            final_score = w_score # Fallback
            
        return best_match, final_score

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
        """Ana OCR döngüsü — hata alsa da kontrollü şekilde tekrar başlatır."""
        global cfg
        restart_attempt = 0

        while self.running:
            try:
                cfg = load_config()  # Launcher'da değişmiş olabilir
                engine = get_ocr_engine()

                if engine == "winocr":
                    self._run_winocr_loop()
                elif engine == "tesseract":
                    self._run_tesseract_loop()
                else:
                    logging.error("OCR Motoru başlatılamadığı için thread beklemeye alındı.")
                    time.sleep(2.0)

                restart_attempt = 0
                break

            except Exception:
                restart_attempt += 1
                backoff = min(10, 2 ** min(restart_attempt, 5))
                logging.exception(f"[OcrThread] Kritik hata. {backoff}s sonra yeniden denenecek.")
                self.hide_hud_signal.emit()
                time.sleep(backoff)

    def _is_gta_active(self) -> bool:
        """Aktif pencerenin GTA 5 olup olmadığını kontrol eder."""
        try:
            import ctypes
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            
            # 1. Yöntem: Sınıf adı (grcWindow) ile kesin kontrol
            class_name = ctypes.create_unicode_buffer(256)
            ctypes.windll.user32.GetClassNameW(hwnd, class_name, 256)
            if class_name.value == "grcWindow":
                return True
                
            # 2. Yöntem: Pencere başlığı (Title) ile yedek kontrol
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length == 0:
                return False
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            return "Grand Theft Auto V" in buff.value
        except Exception:
            return True  # Hata durumunda devam et

    def _run_winocr_loop(self) -> None:
        """Windows OCR döngüsü: Yalnızca menüdeki seçili (Highlight) satırı bulur ve okur."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        # Ana monitör boyutunu alıp sol kısmı (örneğin %35 genişlik) tam yükseklikle tarayacağız
        with mss.mss() as sct:
            monitor = sct.monitors[1]  # Birincil monitör
            # Monitor alanı: {left, top, width, height}
            scan_rect = {
                "top": monitor["top"],
                "left": monitor["left"],
                "width": min(600, int(monitor["width"] * 0.35)),  # Maksimum 600px veya ekranın %35'i
                "height": monitor["height"]
            }
            
            try:
                while self.running:
                    # 1. GTA Pencere Kontrolü
                    is_gta = self._is_gta_active()
                    if is_gta != self.last_gta_state:
                        self.last_gta_state = is_gta
                        self.gta_window_active_signal.emit(is_gta)
                        logging.debug(f"[DEBUG] GTA Penceresi Aktif: {is_gta}")
                    
                    if not is_gta:
                        self.hide_hud_signal.emit()
                        time.sleep(1)
                        continue

                    # 2. Duraklatma Kontrolü
                    if self.paused:
                        self.hide_hud_signal.emit()
                        time.sleep(1)
                        continue

                    try:
                        # 3. Ekranı Yakala
                        screen_grab = np.array(sct.grab(scan_rect))
                        # BGR formattan HSV formata çevir (Renk maskelemesi HSV'de çok daha stabildir)
                        hsv = cv2.cvtColor(screen_grab, cv2.COLOR_BGRA2BGR)
                        hsv = cv2.cvtColor(hsv, cv2.COLOR_BGR2HSV)
                        
                        # 4. Seçili Şeridin (Highlight) Rengini Maskele
                        # GTA V menüsündeki seçili satır genellikle çok açık gri/beyazdır.
                        # HSV değerleri: Hue(0-180), Saturation(0-255), Value(0-255)
                        # Düşük doygunluk (Saturation < 40) ve yüksek parlaklık (Value > 200) olan pikselleri arıyoruz.
                        lower_white = np.array([0, 0, 200])
                        upper_white = np.array([180, 40, 255])
                        
                        mask = cv2.inRange(hsv, lower_white, upper_white)
                        
                        # 5. Maskedeki Şekilleri (Contours) Bul
                        # Küçük gürültüleri gidermek için morfolojik işlem yapalım
                        kernel = np.ones((1, 5), np.uint8) 
                        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
                        
                        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        
                        highlight_rect = None
                        max_w = 0
                        
                        # 6. Bulunan şekillerden "Menü Şeridi" olmaya en uygununu seç
                        for cnt in contours:
                            x, y, w, h = cv2.boundingRect(cnt)
                            
                            # Menü şeridi yatayda uzun (örn 200-400px), dikeyde incedir.
                            # Garaj ve liste elemanlarında çift satırlı isimler olabildiği için yüksekliği 120'ye kadar esnetiyoruz.
                            # Ayrıca sol kenara yakın olmalıdır (x çok büyük olamaz)
                            if w > 150 and w < 440 and h > 20 and h < 120 and x < 50:
                                # En geniş olanı (gerçek şeridi) alıyoruz (Bazen ufak menü parçaları kopuk olabilir)
                                if w > max_w:
                                    max_w = w
                                    highlight_rect = (x, y, w, h)
                                    
                        # 7. Sadece Şeridi Kırp ve OCR'a Gönder
                        candidates = []
                        if highlight_rect:
                            x, y, w, h = highlight_rect
                            
                            # Güvenlik için şeridi biraz daraltalım/genişletelim ki yazıyı tam alsın
                            y_start = max(0, y - 2)
                            y_end = min(screen_grab.shape[0], y + h + 2)
                            
                            # Etkileşim (Interaction) menüsünde araç isimleri sağa dayalıdır (Örn: < Havok >).
                            # Bu yüzden barın "solundaki" ikonları vs. kırparken sağ tarafını tam uzunlukta bırakmalıyız.
                            x_start = max(0, x + 5) 
                            
                            # X_end'i tam genişlikte (veya sonuna kadar) alıyoruz ki Interaction menüsündeki sağa dayalı araç isimleri kesilmesin.
                            x_end = min(screen_grab.shape[1], x + w)
                            
                            roi_color = screen_grab[y_start:y_end, x_start:x_end]
                            roi_gray = cv2.cvtColor(roi_color, cv2.COLOR_BGRA2GRAY)
                            
                            # Seçili şeritte arka plan BEYAZ, metin SİYAHtır.
                            # OCR daha iyi okusun diye resmi Invert (Ters Çevirme) yapıyoruz: Siyah arkaplan, beyaz metin.
                            _, roi_binary = cv2.threshold(roi_gray, 180, 255, cv2.THRESH_BINARY_INV)
                            
                            # Metni okumayı kolaylaştırmak için 2 kat büyüt
                            roi_2x = cv2.resize(roi_binary, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                            
                            # OCR işlemini başlat (Sadece 50x300 piksellik bir alanı okuyor!)
                            lines = self._run_winocr(roi_2x)
                            
                            for line in lines:
                                raw_text = line.text.strip()
                                # print(f"[TARGETED OCR] Ham Metin: '{raw_text}'")
                                
                                clean = self._clean_text(raw_text)
                                if clean:
                                    match_result = self._match_vehicle(clean)
                                    if match_result:
                                        match, score = match_result
                                        candidates.append((match, score, clean))
                                        
                        # 8. Sonuç Değerlendirmesi
                        if candidates:
                            # Sadece 1 satır/araç olmasını bekliyoruz zaten, ilkini alabiliriz.
                            best_match, best_score, best_clean = candidates[0]
                            
                            detected = True
                            last_seen = time.time()
                            
                            if best_match != last_matched:
                                last_matched = best_match
                                logging.debug(f"[OCR SEÇİLDİ] {best_clean} -> {best_match} (Skor: {best_score})")
                                self.vehicle_found_signal.emit(self.search_dict[best_match])
                        
                        else:
                            # Araç kaybolursa zaman aşımından sonra HUD'ı gizle
                            if last_matched != "" and (time.time() - last_seen > self.HUD_TIMEOUT):
                                self.hide_hud_signal.emit()
                                last_matched = ""
                    
                    except Exception as e:
                        logging.exception(f"[OcrThread:winocr] OCR döngüsü hatası: {e}")
                        self.hide_hud_signal.emit()
                        last_matched = ""
                        time.sleep(1.0)

                    time.sleep(0.25) # İstediğiniz hızda okuması için döngü beklemesi
            finally:
                if self._loop:
                    self._loop.close()

    def _run_tesseract_loop(self) -> None:
        """Tesseract döngüsü: Kontur tabanlı, ROI bazlı OCR."""
        last_matched = ""
        last_seen = time.time()

        with mss.mss() as sct:  # Context manager
            monitor = sct.monitors[1]
            scan_rect = {
                "top": monitor["top"],
                "left": monitor["left"],
                "width": min(600, int(monitor["width"] * 0.35)),
                "height": monitor["height"]
            }
            
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
                        screen_grab = np.array(sct.grab(scan_rect))
                        gray = cv2.cvtColor(screen_grab, cv2.COLOR_BGRA2GRAY)
                        
                        _, mask = cv2.threshold(gray, 140, 255, cv2.THRESH_BINARY)
                        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        detected = False
                        
                        for cnt in contours:
                            x, y, w, h = cv2.boundingRect(cnt)
                            
                            # Ölçekli eşik değerleri kontrolü
                            min_w = self.MIN_CONTOUR_WIDTH * self.scale_factor
                            max_w = self.MAX_CONTOUR_WIDTH * self.scale_factor
                            min_h = self.MIN_CONTOUR_HEIGHT * self.scale_factor
                            max_h = self.MAX_CONTOUR_HEIGHT * self.scale_factor
                            
                            if not (min_w < w < max_w and min_h < h < max_h):
                                        continue
                                        
                            # HEURISTIC: Oyun içi çevre yazıları sol sınırdan uzaktır
                            max_x_allowed = 225 * self.scale_factor
                            if x > max_x_allowed:
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
                    
                    except Exception:
                        logging.exception("[OcrThread:tesseract] OCR döngüsü hatası")
                        self.hide_hud_signal.emit()
                        last_matched = ""
                        time.sleep(1.0)

                    time.sleep(0.35)
            finally:
                # Cleanup
                self.hide_hud_signal.emit()