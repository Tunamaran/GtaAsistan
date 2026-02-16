import cloudscraper
import requests
from bs4 import BeautifulSoup
import json
import time
import random
import warnings
import os

# --- UYARILARI GİZLE ---
from bs4 import XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# --- AYARLAR ---
OUTPUT_FILE = "gta_tum_araclar.json"
SITEMAP_URL = "https://www.gtabase.com/sitemap-4seo.xml"
BASE_VEHICLE_URL = "https://www.gtabase.com/grand-theft-auto-v/vehicles/"

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Referer": "https://www.gtabase.com/"
}

# Bot korumalarını aşmak için Cloudscraper başlatılıyor
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'mobile': False
    }
)

def clean_text(text):
    """Metin içindeki gereksiz boşlukları, tabları ve satır atlamaları temizler."""
    if text:
        return ' '.join(text.split())
    return "Veri Yok"

# --- LOGLAMA YARDIMCISI ---
logger_callback = print

def log(message, end="\n"):
    """GUI veya konsol için loglama fonksiyonu."""
    if logger_callback == print:
        print(message, end=end)
    else:
        # GUI için sadece mesajı gönder (end karakteri genellikle GUI'de yeni satır demektir)
        logger_callback(str(message))

# --- 1. ADIM: SİTE HARİTASINI TARAMA ---
def get_all_vehicle_links():
    log(f"1. ADIM: Site Haritası analiz ediliyor ({SITEMAP_URL})...")
    links = set()
    visited_sitemaps = set()
    
    def fetch_sitemap(url):
        if url in visited_sitemaps: return
        visited_sitemaps.add(url)
        
        log(f"   >> Taranıyor: {url}")
        try:
            res = scraper.get(url, headers=headers, timeout=15)
            if res.status_code != 200:
                log(f"   !!! Erişim Hatası: {res.status_code} ({url})")
                return
            
            # XML parser yerine html.parser kullanımı (lxml bağımlılığını kaldırmak için)
            soup = BeautifulSoup(res.content, "html.parser")
            
            for loc in soup.find_all("loc"):
                link = loc.text.strip()
                
                if link.endswith(".xml") and link != url:
                    fetch_sitemap(link)
                
                elif link.startswith(BASE_VEHICLE_URL):
                    path_after_base = link.replace(BASE_VEHICLE_URL, "").strip('/')
                    if '/' not in path_after_base and path_after_base != "":
                        blacklist = ["category", "feed", "search", "page", "brands", "manufacturers"]
                        if not any(b in path_after_base for b in blacklist):
                            links.add(link)
                        
        except Exception as e:
            log(f"   Hata ({url}): {e}")

    fetch_sitemap(SITEMAP_URL)
    log(f"\n   >>> TOPLAM {len(links)} EŞSİZ ARAÇ LİNKİ BULUNDU! <<<")
    return list(links)

def get_vehicle_details(url: str):
    """Tek bir araç sayfasından tüm bilgileri çeker."""
    try:
        res = scraper.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            log(f"   !!! Erişim Hatası: {res.status_code}")
            return None
        
        soup = BeautifulSoup(res.content, "html.parser")
        vehicle_data = {"Link": url}
        
        # Başlık (Vehicle Name)
        title_tag = soup.find("h1", class_="entry-title")
        if title_tag:
            vehicle_data["Vehicle Name"] = clean_text(title_tag.get_text())
        
        # Tüm table satırlarını topla
        for row in soup.find_all("tr"):
            th = row.find("th")
            td = row.find("td")
            if th and td:
                key = clean_text(th.get_text())
                value = clean_text(td.get_text())
                vehicle_data[key] = value
        
        # Resim URL'si
        img_tag = soup.select_one("div.vehicle-image img")
        if img_tag and img_tag.get("src"):
            vehicle_data["Image URL"] = img_tag["src"]
        else:
            vehicle_data["Image URL"] = "Resim Bulunamadı"
        
        return vehicle_data
    except Exception as e:
        log(f"   Hata: {e}")
        return None

def save_data(data: list, filename: str):
    """JSON verisini atomik şekilde kaydeder."""
    import tempfile
    temp_fd, temp_path = tempfile.mkstemp(dir=".", prefix=".tmp_", suffix=".json", text=True)
    try:
        with os.fdopen(temp_fd, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        # Atomik taşıma
        if os.path.exists(filename):
            os.replace(temp_path, filename)
        else:
            os.rename(temp_path, filename)
    except Exception as e:
        # Hata durumunda temp dosyayı temizle
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except:
                pass
        raise e

# --- ANA DÖNGÜ (GUI İÇİN) ---
def run_update(callback=None, incremental=False):
    """GUI tarafından çağrılan güncelleme fonksiyonu."""
    global logger_callback
    if callback:
        logger_callback = callback
    
    main(incremental)

# --- ANA DÖNGÜ ---
def main(incremental=False):
    vehicle_links = get_all_vehicle_links()
    
    if not vehicle_links:
        log("HATA: Araç linki bulunamadı. Sitemap yapısını veya bağlantınızı kontrol edin.")
        return

    all_vehicles = []
    processed_links = set()
    
    # Mevcut veriyi yükle (Incremental mod veya kaza kurtarma için)
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                if isinstance(existing_data, list):
                    all_vehicles = existing_data
                    # Linkleri kümeye ekle
                    for v in all_vehicles:
                        if "Link" in v:
                            processed_links.add(v["Link"])
            log(f"Mevcut Veritabanı: {len(all_vehicles)} araç yüklü.")
        except Exception as e:
            log(f"Mevcut dosya okunamadı: {e}")

    # Linkleri filtrele
    links_to_download = []
    if incremental:
        links_to_download = [link for link in vehicle_links if link not in processed_links]
        log(f"Filtreleme Sonucu: {len(links_to_download)} yeni araç indirilecek.")
        if not links_to_download:
            log("Veritabanınız zaten güncel! İndirilecek yeni araç yok.")
            return
    else:
        log("Tam İndirme Modu: Tüm araçlar sıfırdan indirilecek...")
        links_to_download = vehicle_links
        # Sıfırdan başlıyorsak listeyi temizle (veya üzerine yazılacak)
        if not incremental:
             all_vehicles = [] 
             processed_links = set()

    total = len(links_to_download)
    log(f"\n2. ADIM: {total} Araç indiriliyor...")
    
    try:
        for i, link in enumerate(links_to_download):
            car_name = link.split("/")[-1]
            log(f"[{i+1}/{total}] {car_name} indiriliyor...")
            
            vehicle_data = get_vehicle_details(link)
            if vehicle_data:
                all_vehicles.append(vehicle_data)
            else:
                log(f"[{i+1}/{total}] {car_name} ATLANDI.")
            
            # OTOMATİK YEDEKLEME
            if (i + 1) % 10 == 0:
                save_data(all_vehicles, OUTPUT_FILE)
                log(f"   [!] Ara Kayıt: {len(all_vehicles)} araç toplam.")
            
            time.sleep(random.uniform(0.5, 1.5))

    except KeyboardInterrupt:
        log("\n\n!!! İŞLEM DURDURULDU !!!")
        
    finally:
        if all_vehicles:
            save_data(all_vehicles, OUTPUT_FILE)
            log(f"\n--- İŞLEM BİTTİ ---")
            log(f"Başarıyla tamamlandı! Toplam {len(all_vehicles)} araç veritabanında.")
        else:
            log("\nHiç araç verisi toplanamadı.")

if __name__ == "__main__":
    main()