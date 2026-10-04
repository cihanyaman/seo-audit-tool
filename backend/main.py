"""
SEO Denetim ve Icerik Oneri Araci - Ana API
---------------------------------------------
Calistirmak icin:
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

Sonra frontend/index.html dosyasini tarayicida acabilir ya da
`python -m http.server` ile sunabilirsin.
"""

import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl

from content_suggester import icerik_onerisi_uret
from seo_audit import denetim_yap

load_dotenv()

app = FastAPI(title="SEO Denetim ve Icerik Oneri Araci", version="0.1.0")

# Gelistirme asamasinda tum originlere izin veriyoruz; production'da
# bunu spesifik frontend adresinle sinirlandirmalisin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class DenetimIstegi(BaseModel):
    url: HttpUrl


class IcerikIstegi(BaseModel):
    metin: str
    hedef_anahtar_kelime: str | None = None


@app.get("/")
def kok():
    return {"durum": "calisiyor", "endpointler": ["/denetim", "/icerik-onerisi"]}


@app.post("/denetim")
async def teknik_denetim(istek: DenetimIstegi):
    """Verilen URL icin teknik SEO denetimi calistirir ve skor doner."""
    pagespeed_key = os.environ.get("PAGESPEED_API_KEY")
    try:
        sonuc = await denetim_yap(str(istek.url), pagespeed_api_key=pagespeed_key)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Sayfa analiz edilemedi: {exc}")

    return {
        "url": sonuc.url,
        "toplam_skor": sonuc.toplam_skor,
        "kategori_skorlari": sonuc.kategori_skorlari,
        "bulgular": sonuc.bulgular,
    }


@app.post("/icerik-onerisi")
def icerik_onerisi(istek: IcerikIstegi):
    """Verilen metin icin AI destekli SEO icerik onerileri uretir."""
    if not istek.metin.strip():
        raise HTTPException(status_code=400, detail="Metin bos olamaz.")

    sonuc = icerik_onerisi_uret(istek.metin, istek.hedef_anahtar_kelime)
    if "hata" in sonuc:
        raise HTTPException(status_code=502, detail=sonuc["hata"])
    return sonuc
