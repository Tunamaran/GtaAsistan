# database.py
"""Araç veritabanı ve garaj yönetimi modülü."""
import json
import re
import os
import tempfile
import threading
from typing import Optional, Tuple, List, Dict

# === Garaj Sistemi ===
GARAGE_FILE = "garajim.json"

# Basit dosya cache (Tekrar tekrar disk okumasını önler)
_garage_cache: Optional[List[str]] = None
_garage_mtime: float = 0
_garage_lock = threading.Lock()  # Thread-safe erişim için

def load_garage() -> List[str]:
    """Kayıtlı araç listesini yükler (cache destekli, thread-safe)."""
    global _garage_cache, _garage_mtime
    
    with _garage_lock:
        if not os.path.exists(GARAGE_FILE):
            _garage_cache = []
            return []
        
        try:
            current_mtime = os.path.getmtime(GARAGE_FILE)
            # Cache hâlâ geçerliyse dosyadan tekrar okuma
            if _garage_cache is not None and current_mtime <= _garage_mtime:
                return list(_garage_cache)  # Kopya döndür
            
            with open(GARAGE_FILE, "r", encoding="utf-8") as f:
                _garage_cache = json.load(f)
                _garage_mtime = current_mtime
                return list(_garage_cache)  # Kopya döndür
        except (json.JSONDecodeError, IOError) as e:
            print(f"[UYARI] Garaj dosyası okunamadı: {e}")
            return []

def save_garage(garage_list: List[str]) -> None:
    """Listeyi dosyaya atomik şekilde kaydeder ve cache'i günceller (thread-safe)."""
    global _garage_cache, _garage_mtime
    
    with _garage_lock:
        temp_fd = None
        temp_path = None
        try:
            # Atomik yazma: temp file + rename
            dir_path = os.path.dirname(GARAGE_FILE) or "."
            temp_fd, temp_path = tempfile.mkstemp(dir=dir_path, prefix=".tmp_garage_", suffix=".json", text=True)
            
            with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
                temp_fd = None  # fdopen aldı
                json.dump(garage_list, f, indent=4, ensure_ascii=False)
            
            # Atomik taşıma
            if os.path.exists(GARAGE_FILE):
                os.replace(temp_path, GARAGE_FILE)
            else:
                os.rename(temp_path, GARAGE_FILE)
            
            # Cache'i güncelle
            _garage_cache = list(garage_list)
            _garage_mtime = os.path.getmtime(GARAGE_FILE)
        except IOError as e:
            print(f"[HATA] Garaj kaydedilemedi: {e}")
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

def toggle_vehicle_ownership(vehicle_name: str) -> bool:
    """Aracı varsa siler, yoksa ekler. Sonuç: True=eklendi, False=silindi. Thread-safe."""
    with _garage_lock:
        garage = load_garage()
        if vehicle_name in garage:
            garage.remove(vehicle_name)
            status = False
        else:
            garage.append(vehicle_name)
            status = True
        save_garage(garage)
        return status

def parse_number(text_val: Optional[str]) -> float:
    """Metin içinden sayısal değer çıkarır."""
    if not text_val or text_val == "FREE":
        return 0.0
    nums = re.findall(r"[-+]?\d*\.\d+|\d+", str(text_val).replace(',', ''))
    return float(nums[0]) if nums else 0.0

# === Garaj İstatistikleri ===
def get_garage_stats(db_data: List[Dict]) -> Tuple[int, str]:
    """Garajdaki araç sayısını ve toplam değerini hesaplar."""
    my_garage = load_garage()
    total_count = len(my_garage)
    total_value = 0.0
    
    # Hızlandırmak için isim->fiyat sözlüğü oluştur
    price_map = {car.get("Vehicle Name"): car.get("GTA Online Price", "0") for car in db_data}
    
    for v_name in my_garage:
        if v_name in price_map:
            price = parse_number(price_map[v_name])
            total_value += price
            
    # Formatlı string döndür (Örn: $125,000,000)
    formatted_value = "${:,.0f}".format(total_value)
    return total_count, formatted_value

# === Veritabanı Yükleme ===
def load_vehicle_database() -> Tuple[Dict, List[Dict]]:
    """Ana araç veritabanını yükler."""
    try:
        with open("gta_tum_araclar.json", "r", encoding="utf-8") as f:
            db_data = json.load(f)
            search_dict = {} 
            for car in db_data:
                full_name = car.get("Vehicle Name", "")
                manufacturer = car.get("Manufacturer", "")
                clean_name = full_name
                if manufacturer and full_name.startswith(manufacturer):
                    clean_name = full_name[len(manufacturer):].strip()
                search_dict[clean_name] = car 
            return search_dict, db_data
    except FileNotFoundError:
        print("[HATA] gta_tum_araclar.json dosyası bulunamadı!")
        return {}, []
    except (json.JSONDecodeError, IOError) as e:
        print(f"[HATA] Veritabanı okunamadı: {e}")
        return {}, []

# === Akıllı Etiketler ===
def get_smart_badges(vehicle_data: Dict, for_hud: bool = False) -> List[Tuple[str, str]]:
    """Araç verilerine göre uygun etiketleri döndürür.
    
    Args:
        for_hud: True ise HUD (OCR) bağlamı — SAHİPSİN rozeti atlanır
                 çünkü menülerde sadece sahip olunan araçlar görünür.
    """
    price = parse_number(vehicle_data.get("GTA Online Price", "0"))
    speed = parse_number(vehicle_data.get("Top Speed (Broughy)", "0"))
    accel = parse_number(vehicle_data.get("Stat - Acceleration", "0"))
    bulletproof = str(vehicle_data.get("Bulletproof", "No"))
    features = str(vehicle_data.get("Vehicle Features", ""))
    
    vehicle_name = vehicle_data.get("Vehicle Name", "")

    badges = []
    
    # Araç özelliklerini kontrol et
    if "Yes" in bulletproof:
        badges.append(("🛡️ ZIRHLI", "#0984e3"))
    if "Weaponized" in features:
        badges.append(("⚔️ SİLAHLI", "#d63031"))
    if price <= 1200000 and speed >= 115:
        badges.append(("🔥 F/P CANAVARI", "#e17055"))
    if price >= 2500000:
        badges.append(("💎 LÜKS", "#fdcb6e"))
    if accel >= 90:
        badges.append(("⚡ ROKET", "#6c5ce7"))
    
    # Hiçbir özellik yoksa STANDART etiketini ekle
    if not badges:
        badges.append(("🚙 STANDART", "#636e72"))

    # SAHİPLİK Durumu — Sadece Galeri'de göster (HUD'da gereksiz,
    # çünkü mekanik/pegasus menülerinde zaten sadece sahip olunan araçlar var)
    if not for_hud:
        my_garage = load_garage()
        if vehicle_name in my_garage:
            badges.insert(0, ("✅ SAHİPSİN", "#2ecc71"))
        
    return badges


# === Araç Kullanım Danışmanı ===
def get_vehicle_advice(vehicle_data: Dict, db_data: List[Dict]) -> List[Tuple[str, str]]:
    """OCR ile tespit edilen araç için kullanım tavsiyeleri üretir.
    
    NOT: GTA Online'da mekanik/pegasus/etkileşim menülerinde sadece
    oyuncunun sahip olduğu araçlar görünür. Bu yüzden "satın al" değil,
    "bu aracı ne zaman kullan" odaklı tavsiyeler üretir.
    """
    advice = []
    
    vehicle_name = vehicle_data.get("Vehicle Name", "")
    vehicle_class = vehicle_data.get("Vehicle Class", "")
    speed = parse_number(vehicle_data.get("Top Speed (Broughy)", "0"))
    
    if not vehicle_class or not vehicle_name:
        return advice
    
    # Aynı sınıftaki TÜM araçları bul (veritabanından)
    class_vehicles = [v for v in db_data if v.get("Vehicle Class") == vehicle_class]
    
    if not class_vehicles or speed <= 0:
        return advice
    
    # Sınıf içi hız sıralaması hesapla
    class_speeds = sorted(
        [(v.get("Vehicle Name", ""), parse_number(v.get("Top Speed (Broughy)", "0"))) 
         for v in class_vehicles],
        key=lambda x: x[1], reverse=True
    )
    
    # Bu aracın sırasını bul
    rank = 1
    for name, spd in class_speeds:
        if name == vehicle_name:
            break
        if spd > 0:
            rank += 1
    
    total_in_class = len([s for s in class_speeds if s[1] > 0])
    
    # 1. Sınıfının en hızlısı mı?
    if rank == 1:
        advice.append(("🏅 SINIFININ EN HIZLISI!", "#00b894"))
    elif rank <= 3:
        advice.append((f"🥈 Sınıf hız sırası: {rank}/{total_in_class}", "#74b9ff"))
    elif total_in_class > 0:
        advice.append((f"📊 Sınıf hız sırası: {rank}/{total_in_class}", "#AAAAAA"))
    
    # 2. Bu sınıfta kaç aracın var? (garajdakiler)
    my_garage = load_garage()
    owned_in_class = [v for v in class_vehicles if v.get("Vehicle Name", "") in my_garage]
    if len(owned_in_class) > 1:
        advice.append((f"🏠 Bu sınıfta {len(owned_in_class)} aracın var", "#636e72"))
    
    # 3. Garajındaki en hızlı mı bu sınıfta?
    if len(owned_in_class) > 1:
        owned_speeds = sorted(
            owned_in_class,
            key=lambda v: parse_number(v.get("Top Speed (Broughy)", "0")),
            reverse=True
        )
        fastest_owned = owned_speeds[0].get("Vehicle Name", "")
        if fastest_owned == vehicle_name:
            advice.append(("⭐ Garajındaki en hızlı!", "#ffeaa7"))
        else:
            advice.append((f"💨 Daha hızlın var: {fastest_owned}", "#ffeaa7"))
    
    return advice