import os
import sys
import argparse
import asyncio
from dotenv import load_dotenv

# Pastikan output konsol Windows mendukung karakter UTF-8 dan emoji
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Muat variabel lingkungan dari .env
load_dotenv()


def run_cli(query: str, limit: int):
    """Menjalankan scraping langsung dari terminal tanpa Telegram."""
    from scraper.gmaps_scraper import GoogleMapsScraper
    from exporter.csv_exporter import export_to_csv

    headless = os.getenv("HEADLESS_MODE", "true").lower() == "true"
    timeout_ms = int(os.getenv("BROWSER_TIMEOUT_MS", "60000"))

    print("=" * 65)
    print("🚀 UMKM POS LEAD SCRAPER - CLI MODE")
    print(f"🎯 Target Query : {query}")
    print(f"🔢 Limit Data   : {limit} UMKM")
    print(f"🖥️  Headless Mode: {headless}")
    print("=" * 65)

    scraper = GoogleMapsScraper(headless=headless, timeout_ms=timeout_ms)
    
    async def _execute():
        data = await scraper.scrape(query=query, limit=limit)
        if not data:
            print("\n❌ Tidak ada data yang berhasil diekstrak.")
            return

        csv_file = export_to_csv(data, query=query)
        print("\n" + "=" * 65)
        print("✅ REKAP HASIL SCRAPING:")
        print(f"📁 Lokasi File CSV: {csv_file}")
        
        wa_count = sum(1 for r in data if r.get("phone_info", {}).get("is_mobile", False))
        print(f"📊 Total Data Ditemukan : {len(data)}")
        print(f"📱 Kontak WhatsApp Aktif : {wa_count}")
        print("=" * 65)
        print("\nPratinjau 3 Data Teratas:")
        for idx, item in enumerate(data[:3], start=1):
            p = item.get("phone_info", {})
            print(f" {idx}. {item.get('name')} [{item.get('category')}]")
            print(f"    Rating: {item.get('rating')} ({item.get('reviews_count')} ulasan)")
            print(f"    Alamat: {item.get('address')[:60]}...")
            print(f"    Kontak: {p.get('clean') or 'N/A'} -> WA: {p.get('wa_link') or '-'}")
            print("-" * 50)

    asyncio.run(_execute())

def main():
    parser = argparse.ArgumentParser(description="UMKM POS Lead Scraper & Telegram Bot")
    parser.add_argument(
        "--mode",
        choices=["bot", "cli"],
        default="bot",
        help="Mode operasi: 'bot' untuk menjalankan Telegram Bot, 'cli' untuk scraping via terminal."
    )
    parser.add_argument(
        "--query",
        type=str,
        default="Cafe Bandung",
        help="Kata kunci pencarian untuk mode CLI (contoh: 'Kedai Kopi Tebet')."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Jumlah data target untuk mode CLI (default: 10)."
    )

    args = parser.parse_args()

    if args.mode == "bot":
        from bot.telegram_bot import run_telegram_bot
        run_telegram_bot()
    elif args.mode == "cli":
        run_cli(query=args.query, limit=args.limit)

if __name__ == "__main__":
    main()
