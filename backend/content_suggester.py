"""
AI Destekli Icerik SEO Oneri Modulu
-------------------------------------
Kullanicinin girdigi metni Claude API'ye gondererek, hedef anahtar
kelimeye gore SEO acisindan yapilandirilmis oneriler uretir.

Not: Bu modul disaridan JSON formatinda yanit ister; API cagrisi
basarisiz olursa (anahtar tanimli degil, ag hatasi vb.) anlasilir bir
hata mesaji doner - frontend bunu kullaniciya gosterebilir.
"""

from __future__ import annotations

import json
import os

from anthropic import Anthropic, APIError

SISTEM_PROMPTU = """Sen bir SEO icerik uzmanisin. Sana bir metin ve (varsa) hedef
anahtar kelime verilecek. Yalnizca asagidaki JSON semasina uygun, baska hicbir
aciklama/preamble olmadan JSON dondur:

{
  "okunabilirlik_skoru": <0-100 arasi sayi>,
  "anahtar_kelime_yogunlugu": "<yuzde, orn. '1.8%'>",
  "guclu_yonler": ["<madde>", ...],
  "gelistirme_onerileri": ["<madde>", ...],
  "onerilen_baslik_alternatifleri": ["<baslik1>", "<baslik2>", "<baslik3>"],
  "onerilen_meta_aciklama": "<70-160 karakter arasi meta aciklama onerisi>"
}
"""


def _client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY tanimli degil (.env dosyasini kontrol edin).")
    return Anthropic(api_key=api_key)


def icerik_onerisi_uret(metin: str, hedef_anahtar_kelime: str | None = None) -> dict:
    """Verilen metni analiz edip yapilandirilmis SEO onerileri dondurur."""
    kullanici_mesaji = f"Metin:\n{metin}\n\nHedef anahtar kelime: {hedef_anahtar_kelime or 'belirtilmedi'}"

    try:
        client = _client()
        yanit = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SISTEM_PROMPTU,
            messages=[{"role": "user", "content": kullanici_mesaji}],
        )
        ham_metin = "".join(block.text for block in yanit.content if hasattr(block, "text"))
        temiz = ham_metin.replace("```json", "").replace("```", "").strip()
        return json.loads(temiz)

    except json.JSONDecodeError:
        return {"hata": "AI yanit format hatasi - lutfen tekrar deneyin."}
    except APIError as exc:
        return {"hata": f"Claude API hatasi: {exc}"}
    except RuntimeError as exc:
        return {"hata": str(exc)}
