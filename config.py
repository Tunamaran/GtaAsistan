# config.py
"""Uygulama yapılandırma yönetimi."""
import json
import os
import sys
import copy
import tempfile
from typing import Dict, Any
import logging


VERSION = "18022026.09"

def setup_logging():
    """Loglama yapılandırmasını başlatır."""
    # Program Files gibi korumalı dizinlere yazmaya çalışırsak hata alırız.
    # Bu yüzden logları LocalAppData klasörüne kaydediyoruz.
    # Bu yüzden logları LocalAppData klasörüne kaydediyoruz.
    log_dir = os.path.join(os.getenv('LOCALAPPDATA'), "GtaAsistan")
    os.makedirs(log_dir, exist_ok=True)
    
    global LOG_FILE
    LOG_FILE = os.path.join(log_dir, "debug.log")
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE, encoding='utf-8', mode='w'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    # 3. Parti kütüphanelerin loglarını sustur
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("mss").setLevel(logging.WARNING)

    logging.info("==========================================")
    logging.info(f"GTA Asistan Başlatılıyor... (v{VERSION})")
    logging.info(f"App Dir: {APP_DIR}")
    logging.info(f"Log Dir: {log_dir}")
    logging.info("==========================================")

def get_app_dir() -> str:
    """PyInstaller frozen mod ve normal mod için uygulama dizinini döndürür."""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

APP_DIR = get_app_dir()
# Kullanıcı verilerini LocalAppData içinde sakla
DATA_DIR = os.path.join(os.getenv('LOCALAPPDATA'), "GtaAsistan")
os.makedirs(DATA_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(DATA_DIR, "config.json")

import ctypes

# DPI Awareness flag (sadece bir kez çağrılmalı)
_dpi_aware_set = False

# 2560x1600 için Referans Ayarlar (Baseline)
BASELINE_RESOLUTION = (2560, 1600)


def _get_default_tesseract_path() -> str:
    """Tesseract varsayılan yolunu döndürür (frozen mod desteği)."""
    if getattr(sys, 'frozen', False):
        # Frozen mod (exe): Uygulama dizinindeki tesseract
        return os.path.join(APP_DIR, "tesseract", "tesseract.exe")
    else:
        # Normal mod: Sistem yolu
        return r"C:\Program Files\Tesseract-OCR\tesseract.exe"

BASELINE_CONFIG: Dict[str, Any] = {
    "tesseract_path": _get_default_tesseract_path(),
    "hotkeys": {
        "toggle_gallery": "f11",
        "toggle_ownership": "f9",
        "toggle_ocr": "f10"
    },
    "ocr_region": {
        "top": 0,
        "left": 0,
        "width": 678,  # 2560 px genişlikte
        "height": 635  # 1600 px yükseklikte
    },
    "hud_region": {
        "top": 40,
        "left": 1325, 
        "width": 1215,
        "height": 1510
    },
    "autopilot": True,
    "last_resolution": [2560, 1600], # Son kullanılan çözünürlüğü takip et
    "ui_geometry": {
        "LauncherWindow": {"width": 700, "height": 500, "x": -1, "y": -1},
        "GalleryWindow": {"width": 1200, "height": 800, "x": -1, "y": -1},
        "SettingsWindow": {"width": 600, "height": 900, "x": -1, "y": -1}
    }
}

def get_screen_resolution():
    """Ana ekran çözünürlüğünü (ölçeklendirilmemiş) döndürür."""
    global _dpi_aware_set
    try:
        user32 = ctypes.windll.user32
        # DPI farkındalığını sadece bir kez ayarla
        if not _dpi_aware_set:
            user32.SetProcessDPIAware()
            _dpi_aware_set = True
        w = user32.GetSystemMetrics(0)
        h = user32.GetSystemMetrics(1)
        return w, h
    except:
        return 1920, 1080  # Fallback

def get_scaled_default_config() -> Dict[str, Any]:
    """Mevcut ekran çözünürlüğüne göre ölçeklenmiş varsayılan ayarları döndürür."""
    current_w, current_h = get_screen_resolution()
    base_w, base_h = BASELINE_RESOLUTION
    
    # Oranları Hesapla
    scale_x = current_w / base_w
    scale_y = current_h / base_h
    
    config = copy.deepcopy(BASELINE_CONFIG)
    
    # OCR Bölgesini Ölçekle
    ocr = config["ocr_region"]
    ocr["top"] = int(ocr["top"] * scale_y)
    ocr["left"] = int(ocr["left"] * scale_x)
    ocr["width"] = int(ocr["width"] * scale_x)
    ocr["height"] = int(ocr["height"] * scale_y)
    
    # HUD Bölgesini Ölçekle
    hud = config["hud_region"]
    hud["top"] = int(hud["top"] * scale_y)
    # HUD Left -1 ise (sağdan hizalı) ise dokunma, değilse ölçekle
    if hud["left"] != -1:
        hud["left"] = int(hud["left"] * scale_x)
    hud["width"] = int(hud["width"] * scale_x)
    hud["height"] = int(hud["height"] * scale_y)
    
    config["last_resolution"] = [current_w, current_h]
    
    print(f"[CONFIG] Çözünürlük algılandı: {current_w}x{current_h}. Ayarlar ölçeklendi.")
    return config

def load_config() -> Dict[str, Any]:
    """Config dosyasını yükler, yoksa oluşturur."""
    if not os.path.exists(CONFIG_FILE):
        default_cfg = get_scaled_default_config()
        save_config(default_cfg)
        return default_cfg
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[HATA] Config dosyası okunamadı: {e}")
        return get_scaled_default_config()

def save_config(config_data: Dict[str, Any]) -> None:
    """Config dosyasını atomik şekilde kaydeder."""
    temp_fd = None
    temp_path = None
    try:
        dir_path = os.path.dirname(CONFIG_FILE) or "."
        temp_fd, temp_path = tempfile.mkstemp(dir=dir_path, prefix=".tmp_config_", suffix=".json", text=True)
        
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            temp_fd = None  # fdopen aldı
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        
        # Atomik taşıma
        if os.path.exists(CONFIG_FILE):
            os.replace(temp_path, CONFIG_FILE)
        else:
            os.rename(temp_path, CONFIG_FILE)
    except IOError as e:
        print(f"[HATA] Config kaydedilemedi: {e}")
        # Cleanup
        if temp_fd is not None:
            try:
                os.close(temp_fd)
            except:
                pass
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass

def reset_to_defaults() -> None:
    """Ayarları fabrika varsayılanlarına döndürür (Ölçekli)."""
    default_cfg = get_scaled_default_config()
    save_config(default_cfg)
    print("[BİLGİ] Ayarlar fabrika varsayılanlarına sıfırlandı.")
