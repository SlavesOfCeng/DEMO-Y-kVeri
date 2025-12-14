// app/page.tsx

// 1. Python'dan gelen verinin yapısını TypeScript ile tanımlıyoruz
interface PythonData {
  source: string;
  durum: string;
  aranan_bolum: string;
  sayfa_basligi: string; 
  toplam_kitap: number; 
  toplam_makale: number; // YÖK'ten çektiğimiz sayısal alan eklendi!
}

// Next.js Sunucu Bileşeni
export default async function Home() {
  
  const API_URL = 'http://127.0.0.1:8000/api/data';
  
  let veri: PythonData | null = null;
  let hata: string | null = null;

  try {
    // Python API'sinden veri çekme
    const response = await fetch(API_URL, { 
      // Sunucu taraflı veri çekme için zorunlu:
      cache: 'no-store' 
    });
    
    if (!response.ok) {
      throw new Error(`API hatası: ${response.status}`);
    }

    // 2. Gelen veriyi TypeScript arayüzüne dönüştür
    veri = (await response.json()) as PythonData;
    

  } catch (err) {
    hata = "Python API'ye bağlanılamadı. Lütfen 8000 portunun çalıştığından emin olun.";
  }

return (
    <main className="flex min-h-screen flex-col items-center justify-center p-24 bg-gray-100">
      <h1 className="text-3xl font-bold mb-6 text-indigo-700">
        Bölüm Performans Metrikleri Arayüzü
      </h1>
      
      {hata && (
        <div className="bg-red-100 border border-red-400 text-red-700 p-4 rounded mt-4">
          <p>Bağlantı Hatası: {hata}</p>
        </div>
      )}

      {veri && (
          // Tek kök element kuralına uyulmuştur: Tüm içerik bu div içinde.
          <div className="bg-white p-8 rounded-lg shadow-xl w-full max-w-lg"> 
            <h2 className="text-xl font-semibold mb-4 border-b pb-2">
              Python'dan Çekilen Canlı Veri Raporu
            </h2>
          
            <p className="mb-2">Aranan Bölüm: <span className="text-indigo-600 font-medium">{veri.aranan_bolum}</span></p>
            <p className="mb-4">Kaynak Servis: <strong>{veri.source}</strong></p>

            {/* METRİKLERİN GÖRÜNTÜLENMESİ */}
            <div className="flex gap-4">
              {/* 1. KİTAP METRİĞİ */}
              <div className="p-4 border rounded bg-indigo-50 flex-1 text-center">
                <p className="text-lg font-bold text-gray-700">Toplam Kitap Sayısı:</p>
                <p className="text-4xl font-extrabold text-indigo-700 mt-1">{veri.toplam_kitap}</p>
              </div>

              {/* 2. MAKALE METRİĞİ */}
              <div className="p-4 border rounded bg-green-50 flex-1 text-center">
                <p className="text-lg font-bold text-gray-700">Toplam Makale Sayısı:</p>
                <p className="text-4xl font-extrabold text-green-700 mt-1">{veri.toplam_makale}</p>
              </div>
            </div>
          
            <p className="mt-4 pt-4 border-t">Durum: <span className="text-green-600 font-bold">{veri.durum}</span></p>
          </div>
      )}
    </main>
  );
}