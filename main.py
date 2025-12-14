# --- 1. GEREKLİ KÜTÜPHANELER ---
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import re
import os
import shutil
import pathlib
import subprocess # İşlem öldürmek için
from datetime import datetime
from typing import List, Dict, Any
import json
from threading import Lock, Thread

# --- 2. AYARLAR ---
app = FastAPI()
selenium_lock = Lock() # Driver'ı aynı anda tek işlem kullansın diye
cache_lock = Lock()    # Cache dosyasına aynı anda yazılmasın diye
driver_instance = None 
updating_queries = set() # Şu an güncellenenleri takip et

CACHE_ENABLED = True 
CACHE_FILE = "yok_cache.json"
CACHE_LIFESPAN_SECONDS = 60 # 60 saniye sonra veri "bayat" sayılır

CURRENT_YEAR = datetime.now().year
YEARS_TO_TRACK = [CURRENT_YEAR - i for i in range(5)]

templates = Jinja2Templates(directory="templates")
templates.env.filters["tojson"] = lambda x: json.dumps(x)

# --- 3. YARDIMCI FONKSİYONLAR ---
def normalize_text(text: str) -> str:
    if not text: return ""
    replacements = {'İ': 'i', 'I': 'i', 'ı': 'i', 'Ş': 's', 'ş': 's', 'Ğ': 'g', 'ğ': 'g', 'Ü': 'u', 'ü': 'u', 'Ö': 'o', 'ö': 'o', 'Ç': 'c', 'ç': 'c'}
    text = text.strip()
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text.lower()

# --- 4. CACHE YÖNETİMİ ---
def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except: return {}
    return {}

def save_to_cache(key, data):
    with cache_lock: # Dosya yazma çakışmasını önle
        current_cache = load_cache()
        current_cache[key] = {
            "timestamp": time.time(), 
            "data": data
        }
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(current_cache, f, ensure_ascii=False, indent=4)

# --- 5. DRIVER YÖNETİMİ (NUKE & HEAL) ---
def safe_restart_driver():
    global driver_instance
    print("🔁 Driver güvenli şekilde yeniden başlatılıyor...")
    try:
        if driver_instance:
            driver_instance.quit()
    except:
        pass

    driver_instance = create_driver()


def create_driver():
    """Yeni bir driver oluşturur."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new") 
    options.add_argument("--start-maximized") 
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")
    options.add_argument("--disable-extensions")
    options.add_argument("--dns-prefetch-disable")
    
    prefs = {"profile.managed_default_content_settings.images": 2} 
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--blink-settings=imagesEnabled=false")
    options.page_load_strategy = 'eager'

    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

@app.on_event("startup")
async def startup_event():
    global driver_instance
    safe_restart_driver() # Başlarken temizle
    print("🚀 Sistem başlatılıyor...")
    try:
        driver_instance = create_driver()
        print("✅ Driver Hazır!")
    except Exception as e:
        print(f"⚠️ İlk deneme başarısız: {e}. Tekrar deneniyor...")
        safe_restart_driver()
        try:
            driver_instance = create_driver()
            print("✅ İkinci denemede Driver Hazır!")
        except Exception as final_e:
            print(f"❌ Driver başlatılamadı: {final_e}")

@app.on_event("shutdown")
async def shutdown_event():
    global driver_instance
    if driver_instance:
        try: driver_instance.quit()
        except: pass
        print("🛑 Driver kapatıldı.")

# --- 6. SCRAPING ---
def scrape_publication_counts(driver: webdriver.Chrome, profile_url: str) -> Dict[str, Any]:
    print(f"   -> Veri toplanıyor: {profile_url}")
    driver.set_page_load_timeout(30) # Timeout eklendi

    def create_year_dict():
        return {y: {'Toplam': 0, 'Ulusal': 0, 'Uluslararasi': 0} for y in YEARS_TO_TRACK}

    stats = {
        'Kitaplar': {'Toplam': 0, 'Yillar': {y: 0 for y in YEARS_TO_TRACK}}, 
        'Makaleler': {'Toplam': 0, 'Uluslararasi': 0, 'Ulusal': 0, 'Yillar': create_year_dict()},
        'Bildiriler': {'Toplam': 0, 'Uluslararasi': 0, 'Ulusal': 0, 'Yillar': create_year_dict()},
        'Projeler': {'Toplam': 0, 'Yillar': {y: 0 for y in YEARS_TO_TRACK}} 
    }

    def extract_year(text):
        try:
            matches = re.findall(r'\b(20[0-2][0-9])\b', text)
            if matches: return int(matches[-1])
        except: return None
        return None
    
    try:
        driver.get(profile_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "personelMenu")))
        
        links = {}
        for menu_id, key in [("booksMenu", "Kitaplar"), ("articleMenu", "Makaleler"), 
                             ("proceedingMenu", "Bildiriler"), ("projectMenu", "Projeler")]:
            try: links[key] = driver.find_element(By.CSS_SELECTOR, f"li#{menu_id} a").get_attribute("href")
            except: pass

        if links.get('Kitaplar'):
            try:
                driver.get(links['Kitaplar'])
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.projects")))
                for book in driver.find_elements(By.CSS_SELECTOR, "div.projects div.row"):
                    stats['Kitaplar']['Toplam'] += 1
                    y = extract_year(book.text)
                    if y in YEARS_TO_TRACK: stats['Kitaplar']['Yillar'][y] += 1
            except: pass

        if links.get('Makaleler'):
            try:
                driver.get(links['Makaleler'])
                WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "all")))
                try: driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, 'a[href="#all"]')); time.sleep(0.2)
                except: pass
                
                rows = driver.find_elements(By.CSS_SELECTOR, "div#all tbody tr")
                stats['Makaleler']['Toplam'] = len(rows)
                for row in rows:
                    txt = row.text
                    y = extract_year(txt)
                    intl = "Uluslararası" in txt
                    nat = "Ulusal" in txt
                    if intl: stats['Makaleler']['Uluslararasi'] += 1
                    elif nat: stats['Makaleler']['Ulusal'] += 1
                    if y in YEARS_TO_TRACK:
                        stats['Makaleler']['Yillar'][y]['Toplam'] += 1
                        if intl: stats['Makaleler']['Yillar'][y]['Uluslararasi'] += 1
                        elif nat: stats['Makaleler']['Yillar'][y]['Ulusal'] += 1
            except: pass

        if links.get('Bildiriler'):
            try:
                driver.get(links['Bildiriler'])
                WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "all")))
                try: driver.execute_script("arguments[0].click();", driver.find_element(By.CSS_SELECTOR, 'a[href="#all"]')); time.sleep(0.2)
                except: pass
                rows = driver.find_elements(By.CSS_SELECTOR, "div#all tbody tr")
                if not rows: rows = driver.find_elements(By.CSS_SELECTOR, "tbody.searchable tr")
                stats['Bildiriler']['Toplam'] = len(rows)
                for row in rows:
                    txt = row.text
                    y = extract_year(txt)
                    intl = "Uluslararası" in txt
                    nat = "Ulusal" in txt
                    if intl: stats['Bildiriler']['Uluslararasi'] += 1
                    elif nat: stats['Bildiriler']['Ulusal'] += 1
                    if y in YEARS_TO_TRACK:
                        stats['Bildiriler']['Yillar'][y]['Toplam'] += 1
                        if intl: stats['Bildiriler']['Yillar'][y]['Uluslararasi'] += 1
                        elif nat: stats['Bildiriler']['Yillar'][y]['Ulusal'] += 1
            except: pass

        if links.get('Projeler'):
            try:
                driver.get(links['Projeler'])
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.projectmain")))
                for proj in driver.find_elements(By.CSS_SELECTOR, "div.projectmain"):
                    stats['Projeler']['Toplam'] += 1
                    y = extract_year(proj.text)
                    if y in YEARS_TO_TRACK: stats['Projeler']['Yillar'][y] += 1
            except: pass

    except Exception as e: print(f"Profil Tarama Hatası: {e}")
    return stats

# --- 7. GÜVENLİ ARAMA (OTO-TAMİR İLE) ---
def run_search_with_selenium(query: str) -> List[Dict[str, Any]]:
    global driver_instance
    normalized_key = normalize_text(query)
    
    # Cache kontrolü burada yapmıyoruz, çünkü bu fonksiyon sadece 
    # fiziksel tarama yapmak istendiğinde çağrılıyor.

    # 1. DRIVER SAĞLIK KONTROLÜ
    if driver_instance is None:
        try:
            print("⚠️ Driver yok, oluşturuluyor...")
            driver_instance = create_driver()
        except: return []

    final_items = []
    
    # Thread Lock: Aynı anda sadece bir kişi tarayıcıyı kullanabilir
    with selenium_lock:
        try:
            print(f"🚀 CANLI ARAMA BAŞLATILIYOR: {query}")
            # Bağlantı testi
            try:
                driver_instance.get("https://akademik.yok.gov.tr/AkademikArama/")
            except Exception:
                print("⚠️ Driver yanıt vermiyor! Yeniden başlatılıyor...")
                safe_restart_driver()
                driver_instance = create_driver()
                driver_instance.get("https://akademik.yok.gov.tr/AkademikArama/")

            # Arama İşlemleri
            search_box = WebDriverWait(driver_instance, 10).until(EC.visibility_of_element_located((By.ID, "aramaTerim")))
            search_box.clear()
            search_box.send_keys(query)
            time.sleep(0.2)
            search_box.send_keys(Keys.RETURN)
            
            WebDriverWait(driver_instance, 10).until(EC.presence_of_element_located((By.ID, "authorlistTb")))
            rows = driver_instance.find_elements(By.CSS_SELECTOR, "#authorlistTb h4 a")
            
            target_link = None
            target_name = None
            q_parts = normalize_text(query).split()

            for row in rows:
                txt = row.text.strip()
                norm_txt = normalize_text(txt)
                if all(part in norm_txt for part in q_parts):
                    target_name = txt
                    target_link = row.get_attribute('href')
                    if not target_link.startswith("http"): target_link = f"https://akademik.yok.gov.tr{target_link}"
                    break
            
            if target_link:
                stats = scrape_publication_counts(driver_instance, target_link)
                result_obj = {'Adı': target_name, 'Profil Linki': target_link, 'İstatistikler': stats}
                final_items.append(result_obj)
                
                if CACHE_ENABLED:
                    save_to_cache(normalized_key, result_obj)
                print(f"💾 GÜNCEL VERİ KAYDEDİLDİ: {target_name}")
            else:
                print("❌ İsim bulunamadı.")

        except Exception as e:
            print(f"❌ TARAMA HATASI: {e}")
            # Hata alındıysa driver'ı boz ki bir sonraki sefer yenilensin
            try: driver_instance.quit()
            except: pass
            driver_instance = None
            
    return final_items

# --- 8. ARKA PLAN GÜNCELLEME ---
def background_update(query: str):
    global updating_queries
    norm_key = normalize_text(query)

    # Zaten güncelleniyorsa tekrar kuyruğa alma
    with cache_lock:
        if norm_key in updating_queries: return
        updating_queries.add(norm_key)

    try:
        print(f"🔄 ARKA PLAN GÜNCELLEME BAŞLADI: {query}")
        run_search_with_selenium(query)
    finally:
        with cache_lock:
            updating_queries.discard(norm_key)

# --- 9. ENDPOINTLER ---
@app.get("/", response_class=HTMLResponse)
async def read_panel(request: Request):
    return templates.TemplateResponse("panel.html", {"request": request})

@app.get("/analiz", response_class=HTMLResponse)
async def read_item(request: Request, query: str = None):
    sonuclar = []
    hata = None

    if not query:
        return templates.TemplateResponse("index.html", {"request": request, "sonuclar": [], "years": YEARS_TO_TRACK})

    normalized_key = normalize_text(query)
    cache = load_cache()
    cached_entry = cache.get(normalized_key)
    
    # 1. Cache varsa (eski bile olsa) hemen göster
    if CACHE_ENABLED and cached_entry:
        sonuclar = [cached_entry["data"]]
        
        # Süre kontrolü
        age = time.time() - cached_entry.get("timestamp", 0)
        if age > CACHE_LIFESPAN_SECONDS:
            print(f"⏳ VERİ BAYAT ({int(age)}sn) -> ARKADA GÜNCELLENİYOR...")
            # Arka planda güncelleme başlat (Kullanıcı bekletilmez)
            Thread(target=background_update, args=(query,), daemon=True).start()
        else:
            print("⚡ CACHE TAZE -> GÖSTERİLDİ")

    # 2. Cache yoksa mecburen bekletip çekiyoruz
    else:
        print("🚨 CACHE YOK -> CANLI ÇEKİLİYOR...")
        try:
            sonuclar = run_search_with_selenium(query)
            if not sonuclar: hata = f"'{query}' bulunamadı."
        except Exception as e:
            hata = f"Hata: {str(e)}"

    return templates.TemplateResponse("index.html", {
        "request": request,
        "sonuclar": sonuclar,
        "aranan": query,
        "hata": hata,
        "years": YEARS_TO_TRACK
    })