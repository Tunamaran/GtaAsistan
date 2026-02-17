import json
import os
import logging
from typing import Dict, Any
from config import load_config, DATA_DIR, APP_DIR

_current_lang = "tr"
_translations: Dict[str, Any] = {}
_fallback_translations: Dict[str, Any] = {}

def load_translations():
    """Yüklü dili config'den okur ve ilgili json dosyasını yükler."""
    global _current_lang, _translations, _fallback_translations
    
    cfg = load_config()
    _current_lang = cfg.get("language", "tr")
    
    # Hedef dil dosyasını yükle
    target_file = os.path.join(APP_DIR, "locales", f"{_current_lang}.json")
    if not os.path.exists(target_file):
        # Eğer APP_DIR içinde yoksa (dev ortamı), belki scriptin yanındadır
        target_file = os.path.join(os.path.dirname(__file__), "locales", f"{_current_lang}.json")

    try:
        if os.path.exists(target_file):
            with open(target_file, "r", encoding="utf-8") as f:
                _translations = json.load(f)
        else:
            logging.warning(f"Locale file not found: {target_file}")
            _translations = {}
    except Exception as e:
        logging.error(f"Error loading locale {_current_lang}: {e}")
        _translations = {}

    # Fallback (Türkçe) yükle (Eğer hedef dil TR değilse)
    if _current_lang != "tr":
        fallback_file = os.path.join(APP_DIR, "locales", "tr.json")
        if not os.path.exists(fallback_file):
             fallback_file = os.path.join(os.path.dirname(__file__), "locales", "tr.json")
             
        try:
            if os.path.exists(fallback_file):
                with open(fallback_file, "r", encoding="utf-8") as f:
                    _fallback_translations = json.load(f)
        except Exception as e:
            logging.error(f"Error loading fallback locale: {e}")

def t(key: str, **kwargs) -> str:
    """
    Verilen anahtara karşılık gelen çeviriyi döndürür.
    Nested key destekler: 'launcher.title' -> json['launcher']['title']
    Format argümanlarını destekler: t('welcome', name='Ali') -> "Hoşgeldin Ali"
    """
    if not _translations:
        load_translations()
    
    keys = key.split(".")
    
    # 1. Ana dilde ara
    val = _get_value(_translations, keys)
    
    # 2. Bulunamazsa fallback dilde ara
    if val is None and _current_lang != "tr":
        val = _get_value(_fallback_translations, keys)
    
    # 3. Hala yoksa key'i döndür
    if val is None:
        return key
    
    # 4. Formatla
    try:
        if isinstance(val, str):
            return val.format(**kwargs)
        return val
    except Exception as e:
        logging.warning(f"Error formatting string '{key}': {e}")
        return val

def _get_value(data, keys):
    current = data
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return None
    return current

# Başlangıçta yükle
load_translations()
