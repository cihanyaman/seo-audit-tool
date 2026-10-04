# SEO Denetim ve İçerik Öneri Aracı

Yazılım mühendisliği tez projesi — bir web sitesi URL'sini teknik SEO
kriterlerine göre denetleyen ve girilen metin için AI destekli (Claude API)
içerik/SEO önerileri sunan araç.

## Proje Yapısı

```
seo-audit-tool/
├── backend/
│   ├── main.py              # FastAPI uygulaması, API uç noktaları
│   ├── seo_audit.py         # Teknik SEO denetim mantığı ve puanlama
│   ├── content_suggester.py # Claude API ile AI destekli içerik önerisi
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

## Kurulum

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # .env dosyasını API anahtarlarınla doldur
uvicorn main:app --reload --port 8000
```

**Gerekli API anahtarları:**
- `ANTHROPIC_API_KEY` — İçerik önerisi modülü için zorunlu. https://console.anthropic.com adresinden alınır.
- `PAGESPEED_API_KEY` — Sayfa hızı denetimi için opsiyonel (yoksa bu kategori otomatik olarak atlanır ve toplam skor kalan kategoriler üzerinden hesaplanır). Google Cloud Console'dan ücretsiz alınır.

### Frontend

Herhangi bir build aracı gerekmez. `frontend/index.html` dosyasını doğrudan
tarayıcıda açabilir ya da basit bir sunucuyla servis edebilirsin:

```bash
cd frontend
python -m http.server 5500
```

Sonra tarayıcıda `http://localhost:5500` adresini aç. `script.js` içindeki
`API_TABAN` değişkeninin backend adresinle (`http://localhost:8000`) eşleştiğinden emin ol.

## API Uç Noktaları

| Metod | Yol | Açıklama |
|---|---|---|
| POST | `/denetim` | `{ "url": "..." }` gönder, teknik SEO skorunu al |
| POST | `/icerik-onerisi` | `{ "metin": "...", "hedef_anahtar_kelime": "..." }` gönder, AI önerilerini al |

## Puanlama Yaklaşımı (Tez için Metodoloji Notu)

Teknik denetim, ağırlıklandırılmış bir kural tabanlı sisteme dayanır
(`seo_audit.py` içindeki `PUANLAMA_AGIRLIKLARI` sözlüğü). Her kategori
(başlık, meta açıklama, heading hiyerarşisi, alt etiketleri, iç/dış link,
mobil uyumluluk, sayfa hızı) ayrı ayrı puanlanır ve toplam skor bu
ağırlıklara göre normalize edilir. Bu yaklaşımın literatürdeki benzer
araçlarla (Lighthouse, Yoast SEO vb.) karşılaştırmalı değerlendirmesi,
tezin "sonuçlar" bölümünde ele alınabilir.

## Sonraki Adımlar / Genişletme Fikirleri

- [ ] Birden fazla sayfayı (site geneli) tarayan toplu denetim modu
- [ ] Denetim geçmişini saklayan basit bir veritabanı (SQLite yeterli)
- [ ] Rakip URL karşılaştırması
- [ ] Test verisi ile puanlama algoritmasının doğrulanması (bilinen SEO araçlarıyla karşılaştırma)
