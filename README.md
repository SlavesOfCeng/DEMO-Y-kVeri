# 🎓 YÖK Akademik - Profil Analiz ve Takip Sistemi

Bu proje, **YÖK Akademik Arama** sistemi üzerinden öğretim üyelerinin akademik verilerini (Makale, Bildiri, Kitap, Proje) otomatik olarak çeken, analiz eden ve görselleştiren **FastAPI** tabanlı bir web uygulamasıdır.


## 🚀 Özellikler

Bu proje, standart bir scraping aracından farklı olarak gelişmiş **hata yönetimi** ve **performans optimizasyonlarına** sahiptir:

* **🛡️ Self-Healing (Kendi Kendini Onaran) Driver:** Selenium WebDriver bozulduğunda, `WinError 193` veya `Connection Refused` hataları aldığında sistem bunu algılar, arka planda temizlik yapar ve driver'ı otomatik olarak yeniden başlatır.
* **⚡ Smart Caching (Stale-While-Revalidate):** Kullanıcı bir profil arattığında:
    * Eğer veri önbellekte varsa **anında** gösterir (0 gecikme).
    * Veri eskiyse kullanıcıyı bekletmez, eski veriyi gösterirken **arka planda (Background Task)** güncel veriyi çeker ve cache'i yeniler.
* **🧹 Otomatik Sistem Temizliği:** Uygulama her başladığında asılı kalan `chrome.exe` işlemlerini ve bozuk önbellek dosyalarını temizler.
* **🔍 Headless Browsing:** Tarayıcı arka planda (görünmez modda) çalışır, kaynak tüketimini minimumda tutar.
* **📊 Yıllık Analiz:** Son 5 yılın verilerini kategorize ederek (Ulusal/Uluslararası) sunar.

## 🛠️ Kullanılan Teknolojiler

* **Python 3.x**
* **FastAPI** (Backend Framework)
* **Selenium & WebDriver Manager** (Web Scraping)
* **Jinja2** (Frontend Templating)
* **Uvicorn** (ASGI Server)
* **Threading & Locks** (Eşzamanlılık Yönetimi)

## ⚙️ Kurulum

Projeyi yerel bilgisayarınızda çalıştırmak için adımları takip edin.

### 1. Projeyi Klonlayın
```bash
git clone https://github.com/SlavesOfCeng/DEMO-Y-kVeri
cd DEMO-Y-kVeri