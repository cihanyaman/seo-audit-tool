"""
Teknik SEO Denetim Modulu
--------------------------
Bir URL'yi analiz ederek baslik, meta aciklama, heading hiyerarsisi,
gorsel alt etiketleri, link yapisi ve (opsiyonel) sayfa hizi kriterlerine
gore 0-100 arasi bir SEO skoru ve kategori bazli kirilim uretir.

Puanlama agirliklari PUANLAMA_AGIRLIKLARI sozlugunde tanimlidir; tez
metninde bu agirliklarin nasil belirlendigini (literatur + kendi
gerekcelerin) aciklaman gerekecek.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


# --- Puanlama agirliklari (toplam 100) -------------------------------------
PUANLAMA_AGIRLIKLARI = {
    "baslik": 15,
    "meta_aciklama": 10,
    "heading_hiyerarsisi": 15,
    "alt_etiketleri": 10,
    "ic_link": 10,
    "dis_link": 5,
    "mobil_uyumluluk": 10,
    "sayfa_hizi": 25,
}

IDEAL_BASLIK_MIN = 30
IDEAL_BASLIK_MAX = 60
IDEAL_META_MIN = 70
IDEAL_META_MAX = 160


@dataclass
class DenetimSonucu:
    url: str
    toplam_skor: float = 0.0
    kategori_skorlari: dict = field(default_factory=dict)
    bulgular: list = field(default_factory=list)  # [{kategori, durum, mesaj, oneri}]
    ham_veri: dict = field(default_factory=dict)


TARAYICI_BASLIKLARI = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
}


async def sayfa_getir(url: str) -> tuple[str, dict]:
    """Verilen URL'nin HTML icerigini ve yanit basliklarini ceker."""
    async with httpx.AsyncClient(follow_redirects=True, timeout=15.0) as client:
        yanit = await client.get(url, headers=TARAYICI_BASLIKLARI)
        yanit.raise_for_status()
        return yanit.text, dict(yanit.headers)


def _bulgu_ekle(sonuc: DenetimSonucu, kategori: str, skor: float, max_skor: float,
                 mesaj: str, oneri: str | None = None) -> None:
    sonuc.kategori_skorlari[kategori] = round(skor, 2)
    sonuc.bulgular.append({
        "kategori": kategori,
        "skor": round(skor, 2),
        "max_skor": max_skor,
        "durum": "iyi" if skor >= max_skor * 0.7 else ("orta" if skor >= max_skor * 0.4 else "kotu"),
        "mesaj": mesaj,
        "oneri": oneri,
    })


def _baslik_analiz(soup: BeautifulSoup, sonuc: DenetimSonucu) -> None:
    agirlik = PUANLAMA_AGIRLIKLARI["baslik"]
    etiket = soup.find("title")
    if not etiket or not etiket.text.strip():
        _bulgu_ekle(sonuc, "baslik", 0, agirlik,
                    "Sayfada <title> etiketi bulunamadi.",
                    "Sayfaya 30-60 karakter arasinda, anahtar kelime iceren bir baslik ekleyin.")
        return

    uzunluk = len(etiket.text.strip())
    if IDEAL_BASLIK_MIN <= uzunluk <= IDEAL_BASLIK_MAX:
        _bulgu_ekle(sonuc, "baslik", agirlik, agirlik,
                    f"Baslik uzunlugu ideal aralikta ({uzunluk} karakter).")
    else:
        oran = min(uzunluk, IDEAL_BASLIK_MAX) / IDEAL_BASLIK_MIN if uzunluk < IDEAL_BASLIK_MIN else IDEAL_BASLIK_MAX / uzunluk
        skor = max(agirlik * min(oran, 1.0) * 0.6, agirlik * 0.2)
        _bulgu_ekle(sonuc, "baslik", skor, agirlik,
                    f"Baslik uzunlugu ideal disinda ({uzunluk} karakter).",
                    f"Basligi {IDEAL_BASLIK_MIN}-{IDEAL_BASLIK_MAX} karakter arasina getirin.")


def _meta_aciklama_analiz(soup: BeautifulSoup, sonuc: DenetimSonucu) -> None:
    agirlik = PUANLAMA_AGIRLIKLARI["meta_aciklama"]
    etiket = soup.find("meta", attrs={"name": "description"})
    icerik = etiket.get("content", "").strip() if etiket else ""

    if not icerik:
        _bulgu_ekle(sonuc, "meta_aciklama", 0, agirlik,
                    "Meta aciklama etiketi bulunamadi veya bos.",
                    "70-160 karakter arasinda, sayfayi ozetleyen bir meta aciklama ekleyin.")
        return

    uzunluk = len(icerik)
    if IDEAL_META_MIN <= uzunluk <= IDEAL_META_MAX:
        _bulgu_ekle(sonuc, "meta_aciklama", agirlik, agirlik,
                    f"Meta aciklama uzunlugu ideal aralikta ({uzunluk} karakter).")
    else:
        skor = agirlik * 0.4
        _bulgu_ekle(sonuc, "meta_aciklama", skor, agirlik,
                    f"Meta aciklama uzunlugu ideal disinda ({uzunluk} karakter).",
                    f"Meta aciklamayi {IDEAL_META_MIN}-{IDEAL_META_MAX} karakter arasina getirin.")


def _heading_analiz(soup: BeautifulSoup, sonuc: DenetimSonucu) -> None:
    agirlik = PUANLAMA_AGIRLIKLARI["heading_hiyerarsisi"]
    h1_listesi = soup.find_all("h1")
    h2_listesi = soup.find_all("h2")

    if len(h1_listesi) == 0:
        _bulgu_ekle(sonuc, "heading_hiyerarsisi", agirlik * 0.2, agirlik,
                    "Sayfada H1 etiketi bulunamadi.",
                    "Sayfaya tek ve anlamli bir H1 baslik etiketi ekleyin.")
    elif len(h1_listesi) > 1:
        _bulgu_ekle(sonuc, "heading_hiyerarsisi", agirlik * 0.5, agirlik,
                    f"Sayfada {len(h1_listesi)} adet H1 etiketi var (1 olmali).",
                    "Sayfada yalnizca bir H1 etiketi kullanin.")
    elif len(h2_listesi) == 0:
        _bulgu_ekle(sonuc, "heading_hiyerarsisi", agirlik * 0.7, agirlik,
                    "H1 mevcut ama alt basliklarda (H2) eksiklik var.",
                    "Icerigi bolumlere ayirmak icin H2 etiketleri ekleyin.")
    else:
        _bulgu_ekle(sonuc, "heading_hiyerarsisi", agirlik, agirlik,
                    "Heading hiyerarsisi (H1/H2) duzgun kurulmus.")


def _alt_etiket_analiz(soup: BeautifulSoup, sonuc: DenetimSonucu) -> None:
    agirlik = PUANLAMA_AGIRLIKLARI["alt_etiketleri"]
    gorseller = soup.find_all("img")
    if not gorseller:
        _bulgu_ekle(sonuc, "alt_etiketleri", agirlik, agirlik, "Sayfada gorsel bulunmuyor.")
        return

    eksik = [g for g in gorseller if not g.get("alt", "").strip()]
    oran_tamam = (len(gorseller) - len(eksik)) / len(gorseller)
    skor = agirlik * oran_tamam
    mesaj = f"{len(gorseller)} gorselden {len(eksik)} tanesinde alt etiketi eksik."
    oneri = "Tum gorsellere aciklayici alt metinleri ekleyin." if eksik else None
    _bulgu_ekle(sonuc, "alt_etiketleri", skor, agirlik, mesaj, oneri)


def _link_analiz(soup: BeautifulSoup, base_url: str, sonuc: DenetimSonucu) -> None:
    domain = urlparse(base_url).netloc
    linkler = soup.find_all("a", href=True)
    ic_linkler = [l for l in linkler if domain in l["href"] or l["href"].startswith("/")]
    dis_linkler = [l for l in linkler if l["href"].startswith("http") and domain not in l["href"]]

    ic_agirlik = PUANLAMA_AGIRLIKLARI["ic_link"]
    dis_agirlik = PUANLAMA_AGIRLIKLARI["dis_link"]

    ic_skor = min(len(ic_linkler) / 5, 1.0) * ic_agirlik
    dis_skor = min(len(dis_linkler) / 2, 1.0) * dis_agirlik

    _bulgu_ekle(sonuc, "ic_link", ic_skor, ic_agirlik,
                f"{len(ic_linkler)} adet ic link bulundu.",
                None if len(ic_linkler) >= 5 else "Sayfa icinde daha fazla ic link (ilgili sayfalara) ekleyin.")
    _bulgu_ekle(sonuc, "dis_link", dis_skor, dis_agirlik,
                f"{len(dis_linkler)} adet dis link bulundu.",
                None if len(dis_linkler) >= 2 else "Guvenilir kaynaklara birkac dis link eklemeyi degerlendirin.")


def _mobil_uyumluluk_analiz(soup: BeautifulSoup, sonuc: DenetimSonucu) -> None:
    agirlik = PUANLAMA_AGIRLIKLARI["mobil_uyumluluk"]
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if viewport and "width=device-width" in viewport.get("content", ""):
        _bulgu_ekle(sonuc, "mobil_uyumluluk", agirlik, agirlik, "Viewport meta etiketi dogru yapilandirilmis.")
    else:
        _bulgu_ekle(sonuc, "mobil_uyumluluk", 0, agirlik,
                    "Viewport meta etiketi eksik veya hatali.",
                    '<meta name="viewport" content="width=device-width, initial-scale=1"> ekleyin.')


async def pagespeed_skor_getir(url: str, api_key: str | None) -> float | None:
    """Google PageSpeed Insights API'sinden performans skorunu (0-100) ceker.
    api_key verilmezse None doner ve bu kategori denetim disi birakilir."""
    if not api_key:
        return None

    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    params = {"url": url, "key": api_key, "strategy": "mobile"}
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            yanit = await client.get(endpoint, params=params)
            yanit.raise_for_status()
            veri = yanit.json()
            skor = veri["lighthouseResult"]["categories"]["performance"]["score"]
            return round(skor * 100, 2)
    except Exception:
        return None


async def denetim_yap(url: str, pagespeed_api_key: str | None = None) -> DenetimSonucu:
    """Ana giris noktasi: verilen URL icin tam SEO denetimi calistirir."""
    sonuc = DenetimSonucu(url=url)
    html, _ = await sayfa_getir(url)
    soup = BeautifulSoup(html, "lxml")

    _baslik_analiz(soup, sonuc)
    _meta_aciklama_analiz(soup, sonuc)
    _heading_analiz(soup, sonuc)
    _alt_etiket_analiz(soup, sonuc)
    _link_analiz(soup, url, sonuc)
    _mobil_uyumluluk_analiz(soup, sonuc)

    hiz_agirlik = PUANLAMA_AGIRLIKLARI["sayfa_hizi"]
    pagespeed_skoru = await pagespeed_skor_getir(url, pagespeed_api_key)
    if pagespeed_skoru is not None:
        skor = (pagespeed_skoru / 100) * hiz_agirlik
        _bulgu_ekle(sonuc, "sayfa_hizi", skor, hiz_agirlik,
                    f"PageSpeed performans skoru: {pagespeed_skoru}/100.")
    else:
        # API anahtari yoksa bu kategoriyi denetim disi birak, toplami buna gore olcekle
        _bulgu_ekle(sonuc, "sayfa_hizi", 0, 0,
                    "PageSpeed API anahtari tanimli degil, bu kategori atlandi.")

    aktif_max_toplam = sum(b["max_skor"] for b in sonuc.bulgular)
    toplam = sum(b["skor"] for b in sonuc.bulgular)
    sonuc.toplam_skor = round((toplam / aktif_max_toplam) * 100, 2) if aktif_max_toplam else 0.0

    return sonuc
