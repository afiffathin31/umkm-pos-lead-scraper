# 🚀 UMKM POS Lead Scraper & Telegram Bot

Sistem scraper cerdas untuk mengekstrak data calon klien potensial bagi sistem **Point of Sale (POS)** dari Google Maps berdasarkan wilayah dan sektor usaha (Cafe, Restoran, Kedai Kopi, Retail, dll). Dilengkapi normalisasi kontak otomatis, link chat WhatsApp langsung (`wa.me`), kalkulator prioritas prospek POS, dan integrasi Telegram Bot interaktif on-demand.

---

## ✨ Fitur Utama

1. **Scraping Google Maps Cerdas (Playwright)**:
   - Meniru interaksi browser nyata dengan scroll dinamis dan delay bertahap untuk menghindari blokir/CAPTCHA.
   - Ekstraksi detail: Nama Bisnis, Kategori, Rating, Jumlah Ulasan, Alamat Lengkap, Nomor Telepon, Website, dan URL Maps.

2. **Lead Enrichment Khusus Sales POS**:
   - **Tautan WhatsApp Otomatis**: Mengonversi nomor seluler Indonesia (`08...`, `+62...`) menjadi tautan `https://wa.me/628...` agar tim sales bisa langsung mengontak pemilik usaha dari CSV dengan 1 klik.
   - **Status Prospek POS**: Otomatis mengelompokkan prospek berdasarkan jumlah ulasan dan rating (misal: review > 50 menandakan tempat usaha ramai yang mendesak butuh efisiensi kasir POS).

3. **Format CSV Ramah Microsoft Excel**:
   - Menggunakan encoding `utf-8-sig` (BOM) sehingga nomor telepon berawalan angka `0` atau `+` tidak rusak atau berubah menjadi notasi ilmiah (*scientific notation*) di Excel Windows.

4. **Telegram Bot On-Demand**:
   - Tim sales cukup mengirimkan perintah di Telegram, misalnya:
     ```text
     /scrape "Bandung Wetan" "Cafe" 25
     ```
   - Bot akan memproses pencarian dan langsung mengunggah file CSV rekap ke ruang obrolan Telegram.
   - Dilengkapi sistem **Whitelist Chat ID** pada `.env` agar server dan bot tidak disalahgunakan pihak luar.

---

## 🛠️ Persyaratan Sistem & Instalasi

Pastikan Python 3.9+ sudah terpasang di komputer Anda.

### 1. Masuk ke Direktori Proyek
```bash
cd C:\Users\Apip\.gemini\antigravity\scratch\umkm-pos-lead-scraper
```

### 2. Pasang Dependensi Python
```bash
pip install -r requirements.txt
```

### 3. Pasang Browser Engine Playwright
```bash
playwright install chromium
```

---

## ⚙️ Konfigurasi `.env`

Salin template file `.env.example` ke `.env` (atau edit file `.env` yang sudah disediakan):

```env
# Telegram Bot Configuration
# Dapatkan token dari @BotFather di Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ

# Whitelist Telegram Chat ID (pisahkan dengan koma jika ada banyak sales/admin)
# Kosongkan jika ingin membuka akses umum saat testing
ALLOWED_CHAT_IDS=123456789

# Konfigurasi Scraper
HEADLESS_MODE=true
DEFAULT_MAX_LIMIT=30
BROWSER_TIMEOUT_MS=60000
```

> **Cara Mendapatkan Chat ID Telegram Anda:**
> 1. Chat ke bot Anda di Telegram dan ketik `/start` atau `/id`.
> 2. Bot akan otomatis menampilkan `Chat ID Anda: XXXXXXXX`.
> 3. Salin ID tersebut ke `ALLOWED_CHAT_IDS` di file `.env`.

---

## 🖥️ Cara Menjalankan

### Opsi A: Mode CLI (Uji Coba Cepat Tanpa Telegram)
Anda bisa langsung melakukan scraping dari terminal komputer untuk menguji coba:

```bash
# Contoh: Cari 5 cafe di Tebet Jakarta Selatan
python main.py --mode cli --query "Cafe Tebet Jakarta Selatan" --limit 5

# Contoh: Cari 10 kedai kopi di Bandung
python main.py --mode cli --query "Kedai Kopi Bandung" --limit 10
```
File CSV hasil rekap akan otomatis tersimpan di folder `exports/`.

---

### Opsi B: Mode Telegram Bot (Layanan Interaktif)
Jalankan bot dengan perintah:

```bash
python main.py --mode bot
```

Buka Telegram Anda dan kirim perintah ke bot:
- `/start` - Menampilkan panduan dan Chat ID Anda.
- `/scrape "<wilayah>" ["<kategori>"] [jumlah]`

**Contoh Perintah Telegram:**
```text
/scrape "Bandung Barat" "Cafe" 20
/scrape "Surabaya Gubeng" "Restoran" 25
/scrape "Kemang Jakarta Selatan" "Kedai Kopi" 30
```

---

## 📂 Struktur Direktori

```text
umkm-pos-lead-scraper/
├── bot/
│   └── telegram_bot.py       # Handler bot Telegram, auth whitelist & file sender
├── scraper/
│   └── gmaps_scraper.py      # Core Google Maps scraper berbasis Playwright
├── exporter/
│   └── csv_exporter.py       # Exporter CSV Excel-compatible & lead scoring
├── utils/
│   └── phone_cleaner.py      # Normalisasi nomor HP & generator link wa.me
├── tests/
│   └── test_phone_cleaner.py # Unit test nomor telepon & parsing
├── exports/                  # Folder penyimpanan output file CSV
├── .env                      # File konfigurasi bot & scraper
├── requirements.txt          # Daftar dependensi Python
├── main.py                   # Entry point aplikasi (CLI & Bot)
└── README.md                 # Dokumentasi panduan lengkap
```
