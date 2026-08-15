# 🚀 YKS / TYT-AYT Kampı & Zihin Haritaları Otomasyon Kurulum Rehberi

Bu proje, `matematğin yolculuğu.pdf` eserindeki bilgileri **Müfit Hoca ile Matematik (`@mufithocailematematik`)** markasıyla ve kaynak **`@riyazihane`** atfıyla her gün **bilgisayarınız kapalıyken bile** Instagram'da otomatik paylaşan tam otonom bir bulut sistemidir.

---

## 📌 1. Sistemin Çalışma Mantığı (Özet)

1. Her sabah Türkiye saati ile **09:00'da** GitHub sunucuları (GitHub Actions) otomatik uyanır.
2. [`data/state.json`](data/state.json) dosyasından sıradaki günün numarasını (Örn: *Gün 9 / 97*) okur.
3. [`data/campaign_97_days.json`](data/campaign_97_days.json) dosyasından o güne ait kancayı, tarihsel hikayeyi, TYT-AYT köprüsünü ve soru çıkartmasını çeker.
4. [`engine/story_generator.py`](engine/story_generator.py) motoru 1080x1920 (9:16) yüksek çözünürlüklü Instagram Hikayesini üretir.
5. Meta Instagram Graph API aracılığıyla doğrudan **Instagram Hikayenizde (Story)** canlı olarak paylaşır.
6. Paylaşılan gün sayısını 1 artırır ve GitHub reposuna otomatik kaydeder (commit & push).

---

## 🔑 2. Instagram API Anahtarlarını Alma (5 Adımda Kurulum)

Bilgisayarınız kapalıyken Instagram'a doğrudan paylaşım yapabilmek için Meta'nın ücretsiz resmi API'si kullanılır:

### Adım 1: Instagram Hesabınızı Profesyonel Yapın
1. Telefonunuzdan Instagram uygulamasını açın.
2. **Ayarlar ve Gizlilik $\to$ Hesap Türü ve Araçları $\to$ Profesyonel Hesaba Geç (İçerik Üretici / Creator veya İşletme)** seçin.

### Adım 2: Bir Facebook Sayfasına Bağlayın
* Meta Graph API, Instagram hesabının bir Facebook Sayfasına bağlı olmasını gerektirir.
* Facebook'ta basit bir sayfa açın (Örn: *Müfit Hoca ile Matematik*) ve Instagram hesabınızı bu sayfaya bağlayın.

### Adım 3: Meta for Developers'da Uygulama Oluşturun
1. [developers.facebook.com](https://developers.facebook.com/) adresine gidin ve Facebook hesabınızla giriş yapın.
2. **Uygulamalarım $\to$ Uygulama Oluştur** butonuna tıklayın.
3. Tür olarak **"Diğer" $\to$ "İşletme" (Business)** seçin.
4. Uygulama adını girip oluşturun.

### Adım 4: Instagram Graph API İzinlerini Alın ve Token Üretin
1. **Graph API Gezgini (Graph API Explorer)** aracına gidin: [developers.facebook.com/tools/explorer](https://developers.facebook.com/tools/explorer/)
2. Oluşturduğunuz uygulamayı seçin.
3. **İzinler (Permissions)** bölümünden şu izinleri ekleyin:
   * `instagram_basic`
   * `instagram_content_publish`
   * `pages_show_list`
   * `pages_read_engagement`
4. **Generate Access Token** butonuna tıklayın ve izinleri onaylayın.
5. Bu token'ı **Kalıcı Token'a (Never-expiring Long-Lived Token)** dönüştürmek için [Meta Access Token Tool](https://developers.facebook.com/tools/debug/accesstoken/) üzerinden *"Extend Access Token"* butonuna basın.

### Adım 5: Instagram Hesap Kimliğinizi (Account ID) Öğrenin
Graph API Explorer'da arama çubuğuna şunu yazıp çalıştırın:
```http
GET me/accounts?fields=instagram_business_account
```
Dönen yanıtta `"instagram_business_account": { "id": "17841400000000000" }` kısmındaki sayı sizin `INSTAGRAM_ACCOUNT_ID` değerinizdir.

---

## ⚙️ 3. GitHub Secrets (Gizli Anahtarlar) Ayarı

GitHub Actions'ın hesabınıza erişebilmesi için anahtarları reponuza ekleyin:

1. Bu projeyi yüklediğiniz **GitHub Reposuna** gidin.
2. **Settings (Ayarlar) $\to$ Secrets and variables $\to$ Actions** sayfasına girin.
3. **New repository secret** butonuna basarak şu iki anahtarı ekleyin:

| Secret Adı | Değer |
| :--- | :--- |
| `INSTAGRAM_ACCOUNT_ID` | 5. Adımda bulduğunuz sayısal Instagram ID |
| `INSTAGRAM_ACCESS_TOKEN` | 4. Adımda aldığınız kalıcı Meta Access Token |

---

## 🧪 4. Sistemi Manuel Test Etme (1 Tıkla Çalıştırma)

Otomasyonun çalıştığını hemen test etmek için:
1. GitHub reponuzda **Actions** sekmesine tıklayın.
2. Sol menüden **"Daily Instagram Story Automation"** iş akışını seçin.
3. Sağdaki **"Run workflow"** butonuna basın.
4. Birkaç saniye içinde günün hikayesi üretilecek, Instagram'a gönderilecek ve `state.json` güncellenecektir!

---

## 📁 5. Proje Dosya Dizini

```
├── .github/workflows/
│   └── daily_camp_publish.yml    # Her sabah 09:00'da çalışan bulut otomasyonu
├── assets/fonts/                 # Tipografi yazı tipleri (Georgia, Palatino, Segoe UI)
├── data/
│   ├── campaign_97_days.json     # 97 günün tüm konu, kanca, köprü ve anket veritabanı
│   └── state.json                # Kaçıncı günde olunduğunu tutan canlı sayaç
├── dist/
│   ├── stories/                  # 1080x1920 Instagram Story çıktıları
│   └── videos/                   # 9:16 Türkçe seslendirmeli Reels videoları
├── engine/
│   ├── story_generator.py        # Yüksek kaliteli Hikaye görsel motoru
│   └── video_generator.py        # Edge-TTS Türkçe sesli Reels video motoru
├── publisher/
│   └── instagram_publisher.py    # Meta Graph API yayınlama modülü
└── setup_guide.md                # Kurulum ve kullanım kılavuzu
```

---

## 🛠️ 6. Yerel Olarak Bilgisayarda Çalıştırma Komutları

* **Günün Hikayesini Yerel Olarak Üret:**
  ```bash
  python publisher/instagram_publisher.py
  ```
* **İstediğin Belirli Bir Günü Üret (Örn: Gün 42):**
  ```bash
  python publisher/instagram_publisher.py --day 42
  ```
* **Türkçe Seslendirmeli Reels Videosu da Üret:**
  ```bash
  python publisher/instagram_publisher.py --video
  ```
