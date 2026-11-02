import os
import shlex
import asyncio
from typing import List
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from scraper.gmaps_scraper import GoogleMapsScraper
from exporter.csv_exporter import export_to_csv

def get_allowed_chat_ids() -> List[int]:
    """Mengambil daftar whitelist Chat ID dari variabel lingkungan."""
    raw = os.getenv("ALLOWED_CHAT_IDS", "").strip()
    if not raw:
        return []
    ids = []
    for item in raw.split(","):
        clean_item = item.strip()
        if clean_item.isdigit() or (clean_item.startswith("-") and clean_item[1:].isdigit()):
            ids.append(int(clean_item))
    return ids

def is_authorized(chat_id: int) -> bool:
    allowed = get_allowed_chat_ids()
    if not allowed:
        # Jika whitelist kosong, izinkan untuk mempermudah setup awal
        return True
    return chat_id in allowed

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan pesan pembuka dan petunjuk penggunaan bot."""
    chat_id = update.effective_chat.id
    auth_status = "✅ Diizinkan" if is_authorized(chat_id) else "⛔ Belum Terdaftar di Whitelist"
    
    msg = (
        "👋 *Halo! Selamat datang di UMKM POS Lead Scraper Bot*\n\n"
        "Bot ini dirancang untuk mencari prospek UMKM (F&B, Retail, Kafe, dll) "
        "di wilayah tertentu, mengekstrak kontak WhatsApp pemilik usaha, "
        "dan mengirimkan rekap file CSV siap follow-up tim sales POS.\n\n"
        f"🆔 *Chat ID Anda:* `{chat_id}`\n"
        f"🛡️ *Status Akses:* {auth_status}\n\n"
        "📌 *Cara Penggunaan Perintah /scrape:*\n"
        "• `/scrape \"Bandung Wetan\" \"Cafe\" 25`\n"
        "• `/scrape \"Jakarta Selatan\" \"Kedai Kopi\" 20`\n"
        "• `/scrape \"Surabaya Gubeng\" \"Restoran\" 30`\n\n"
        "Format parameter:\n"
        "`/scrape \"<wilayah>\" [\"<kategori>\"] [jumlah]`\n"
        "_(Jumlah data default 25, maksimal 50 per pencarian)_"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Perintah cepat untuk mengecek Chat ID user."""
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"🆔 Chat ID Telegram Anda: `{chat_id}`\n"
        f"Salin ID ini ke file `.env` pada baris `ALLOWED_CHAT_IDS=` jika ingin membatasi akses.",
        parse_mode="Markdown"
    )

async def scrape_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler utama untuk memproses perintah scraping UMKM."""
    chat_id = update.effective_chat.id
    if not is_authorized(chat_id):
        await update.message.reply_text(
            f"⛔ *Akses Ditolak*\n"
            f"Chat ID `{chat_id}` belum terdaftar di whitelist bot.\n"
            f"Silakan tambahkan Chat ID ini ke file `.env` di server.",
            parse_mode="Markdown"
        )
        return

    # Parsing argumen dengan shlex agar mendukung kutip dua: /scrape "Bandung Barat" "Cafe" 20
    args_text = update.message.text.replace("/scrape", "", 1).strip()
    if not args_text:
        await update.message.reply_text(
            "⚠️ *Format perintah belum lengkap!*\n\n"
            "Contoh penggunaan yang benar:\n"
            "`/scrape \"Bandung Wetan\" \"Cafe\" 25`\n"
            "`/scrape \"Tebet Jakarta Selatan\" \"Kedai Kopi\" 20`",
            parse_mode="Markdown"
        )
        return

    try:
        parsed_args = shlex.split(args_text)
    except Exception:
        parsed_args = args_text.split()

    if len(parsed_args) == 1:
        # Hanya wilayah atau query utuh
        query = parsed_args[0]
        limit = int(os.getenv("DEFAULT_MAX_LIMIT", 25))
    elif len(parsed_args) == 2:
        if parsed_args[1].isdigit():
            query = parsed_args[0]
            limit = int(parsed_args[1])
        else:
            query = f"{parsed_args[1]} {parsed_args[0]}"
            limit = int(os.getenv("DEFAULT_MAX_LIMIT", 25))
    else:
        # Arg 0: Wilayah, Arg 1: Kategori, Arg 2: Limit
        wilayah = parsed_args[0]
        kategori = parsed_args[1]
        query = f"{kategori} {wilayah}"
        try:
            limit = int(parsed_args[2])
        except ValueError:
            limit = 25

    # Batasi limit aman agar tidak memicu deteksi bot
    if limit < 5:
        limit = 5
    elif limit > 50:
        limit = 50

    status_msg = await update.message.reply_text(
        f"⏳ *Memulai Scraping Google Maps...*\n"
        f"🎯 *Target Pencarian:* `{query}`\n"
        f"🔢 *Target Data:* `{limit}` UMKM\n\n"
        f"Bot sedang membuka browser dan mencari kontak usaha...",
        parse_mode="Markdown"
    )

    last_update_time = [0.0]

    async def on_progress(text: str):
        # Update pesan di Telegram dengan throttling agar tidak kena rate-limit Telegram
        loop = asyncio.get_running_loop()
        now = loop.time()
        if now - last_update_time[0] > 4.0:
            last_update_time[0] = now
            try:
                await status_msg.edit_text(
                    f"⏳ *Sedang Memproses...*\n"
                    f"🎯 *Target:* `{query}`\n"
                    f"📋 *Status:* {text}",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

    try:
        headless = os.getenv("HEADLESS_MODE", "true").lower() == "true"
        timeout_ms = int(os.getenv("BROWSER_TIMEOUT_MS", "60000"))
        scraper = GoogleMapsScraper(headless=headless, timeout_ms=timeout_ms)

        results = await scraper.scrape(query=query, limit=limit, progress_callback=on_progress)

        if not results:
            await status_msg.edit_text(
                f"❌ Tidak ditemukan data UMKM untuk pencarian: `{query}`.\n"
                f"Coba perjelas nama wilayah atau gunakan kata kunci lain.",
                parse_mode="Markdown"
            )
            return

        # Ekspor ke file CSV ramah Excel
        csv_path = export_to_csv(results, query=query)

        # Hitung statistik rekap
        total_data = len(results)
        wa_count = sum(1 for r in results if r.get("phone_info", {}).get("is_mobile", False))
        telp_count = sum(1 for r in results if r.get("phone_info", {}).get("clean", "") and not r.get("phone_info", {}).get("is_mobile", False))
        high_prospect_count = sum(1 for r in results if r.get("reviews_count", 0) >= 50 and r.get("rating", 0) >= 4.0)

        summary_text = (
            f"✅ *Scraping UMKM Berhasil Selesai!*\n\n"
            f"🎯 *Pencarian:* `{query}`\n"
            f"📊 *Total UMKM Didapat:* `{total_data}`\n"
            f"📱 *Kontak WhatsApp:* `{wa_count}` UMKM\n"
            f"☎️ *Telepon Kantor/Kabel:* `{telp_count}` UMKM\n"
            f"⭐ *Prospek Prioritas Tinggi:* `{high_prospect_count}` UMKM\n\n"
            f"File CSV rekap lengkap terlampir di bawah.\n"
            f"_(Dilengkapi kolom tautan chat WhatsApp langsung `wa.me` untuk tim sales)_"
        )

        await status_msg.edit_text("📤 Mengunggah file CSV rekap...", parse_mode="Markdown")

        # Kirim dokumen CSV
        with open(csv_path, "rb") as doc:
            await update.message.reply_document(
                document=doc,
                filename=os.path.basename(csv_path),
                caption=summary_text,
                parse_mode="Markdown"
            )

        # Hapus atau ubah pesan status awal
        await status_msg.delete()

    except Exception as e:
        await status_msg.edit_text(
            f"⚠️ Terjadi error saat menjalankan scraper: `{str(e)}`",
            parse_mode="Markdown"
        )

def run_telegram_bot():
    """Menjalankan bot Telegram polling."""
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("[ERROR] TELEGRAM_BOT_TOKEN belum diset di file .env!")
        print("Silakan edit file .env dan masukkan bot token Anda dari @BotFather.")
        return

    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", start_command))
    app.add_handler(CommandHandler("id", id_command))
    app.add_handler(CommandHandler("scrape", scrape_command))

    print("[Telegram Bot] Bot sedang berjalan... Tekan Ctrl+C untuk menghentikan.", flush=True)
    app.run_polling()

