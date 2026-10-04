// Backend adresi - gelistirme icin localhost, production'da degistirin
const API_TABAN = "http://localhost:8000";

const denetimForm = document.getElementById("denetim-form");
const denetimSonuc = document.getElementById("denetim-sonuc");
const denetimYukleniyor = document.getElementById("denetim-yukleniyor");

const icerikForm = document.getElementById("icerik-form");
const icerikSonuc = document.getElementById("icerik-sonuc");
const icerikYukleniyor = document.getElementById("icerik-yukleniyor");

function durumSinifi(durum) {
  return { iyi: "durum-iyi", orta: "durum-orta", kotu: "durum-kotu" }[durum] || "durum-orta";
}

function hataGoster(konteyner, mesaj) {
  konteyner.innerHTML = `<div class="hata-kutusu">⚠️ ${mesaj}</div>`;
}

denetimForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const url = document.getElementById("url-girisi").value;

  denetimSonuc.innerHTML = "";
  denetimYukleniyor.classList.remove("gizli");

  try {
    const yanit = await fetch(`${API_TABAN}/denetim`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    const veri = await yanit.json();
    if (!yanit.ok) throw new Error(veri.detail || "Bilinmeyen hata");

    let html = `<div class="toplam-skor" style="color:${veri.toplam_skor >= 70 ? '#16a34a' : veri.toplam_skor >= 40 ? '#d97706' : '#dc2626'}">
      ${veri.toplam_skor} / 100
    </div>`;

    veri.bulgular.forEach((b) => {
      html += `
        <div class="bulgu-satir">
          <div>
            <div class="bulgu-baslik">${b.kategori.replace(/_/g, " ")}</div>
            <p class="bulgu-mesaj">${b.mesaj}</p>
            ${b.oneri ? `<p class="bulgu-oneri">💡 ${b.oneri}</p>` : ""}
          </div>
          <span class="durum-etiketi ${durumSinifi(b.durum)}">${b.skor}/${b.max_skor}</span>
        </div>`;
    });

    denetimSonuc.innerHTML = html;
  } catch (hata) {
    hataGoster(denetimSonuc, hata.message);
  } finally {
    denetimYukleniyor.classList.add("gizli");
  }
});

icerikForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const metin = document.getElementById("metin-girisi").value;
  const anahtarKelime = document.getElementById("anahtar-kelime-girisi").value;

  icerikSonuc.innerHTML = "";
  icerikYukleniyor.classList.remove("gizli");

  try {
    const yanit = await fetch(`${API_TABAN}/icerik-onerisi`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ metin, hedef_anahtar_kelime: anahtarKelime || null }),
    });

    const veri = await yanit.json();
    if (!yanit.ok) throw new Error(veri.detail || "Bilinmeyen hata");

    icerikSonuc.innerHTML = `
      <p><strong>Okunabilirlik Skoru:</strong> ${veri.okunabilirlik_skoru}/100</p>
      <p><strong>Anahtar Kelime Yoğunluğu:</strong> ${veri.anahtar_kelime_yogunlugu}</p>

      <p><strong>Güçlü Yönler:</strong></p>
      <ul class="oneri-listesi">${veri.guclu_yonler.map((g) => `<li>${g}</li>`).join("")}</ul>

      <p><strong>Geliştirme Önerileri:</strong></p>
      <ul class="oneri-listesi">${veri.gelistirme_onerileri.map((g) => `<li>${g}</li>`).join("")}</ul>

      <p><strong>Alternatif Başlık Önerileri:</strong></p>
      <ul class="oneri-listesi">${veri.onerilen_baslik_alternatifleri.map((b) => `<li>${b}</li>`).join("")}</ul>

      <p><strong>Önerilen Meta Açıklama:</strong></p>
      <p class="bulgu-mesaj">${veri.onerilen_meta_aciklama}</p>
    `;
  } catch (hata) {
    hataGoster(icerikSonuc, hata.message);
  } finally {
    icerikYukleniyor.classList.add("gizli");
  }
});
