from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time

# Ayarlar
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
# Bot olduğumuzu gizlemeye çalışalım
options.add_argument("--disable-blink-features=AutomationControlled") 
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

print("--- DEDEKTİF BAŞLIYOR ---")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

try:
    print("1. Siteye gidiliyor...")
    driver.get("https://akademik.yok.gov.tr/AkademikArama/")
    
    print("2. Sayfanın yüklenmesi için 10 saniye bekleniyor...")
    time.sleep(10)
    
    # RAPOR 1: Başlık ve Adres
    print(f"\n--- SAYFA RAPORU ---")
    print(f"Görünen Başlık: {driver.title}")
    print(f"Mevcut Adres: {driver.current_url}")
    
    # RAPOR 2: Input (Giriş Kutusu) Sayısı
    inputs = driver.find_elements(By.TAG_NAME, "input")
    print(f"\nSayfada toplam {len(inputs)} adet giriş kutusu (input) bulundu.")
    
    print("Bulunan kutuların detayları:")
    for i, kutu in enumerate(inputs):
        try:
            kutu_id = kutu.get_attribute("id")
            kutu_name = kutu.get_attribute("name")
            kutu_type = kutu.get_attribute("type")
            gorunur_mu = kutu.is_displayed()
            print(f"  {i+1}. Kutu -> ID: '{kutu_id}' | Name: '{kutu_name}' | Type: '{kutu_type}' | Görünür mü: {gorunur_mu}")
        except:
            print(f"  {i+1}. Kutu okunamadı.")

    # RAPOR 3: Iframe Kontrolü
    iframes = driver.find_elements(By.TAG_NAME, "iframe")
    print(f"\nSayfada {len(iframes)} adet IFRAME (iç içe pencere) var.")

    # FOTOĞRAF ÇEK
    driver.save_screenshot("dedektif_kanit.png")
    print("\n✅ EKRAN FOTOĞRAFI ÇEKİLDİ: 'dedektif_kanit.png' dosyasına bak!")

except Exception as e:
    print(f"HATA: {e}")

finally:
    print("\nDedektif işini bitirdi. Tarayıcı kapanıyor...")
    # driver.quit() # Sonucu görmen için kapatmıyorum, istersen bu satırı aç.