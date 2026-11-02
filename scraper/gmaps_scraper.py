import asyncio
import re
import urllib.parse
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
from playwright.async_api import async_playwright
from utils.phone_cleaner import clean_phone_number

class GoogleMapsScraper:
    """Scraper Google Maps menggunakan Playwright async engine."""
    
    def __init__(self, headless: bool = True, timeout_ms: int = 60000):
        self.headless = headless
        self.timeout_ms = timeout_ms

    async def scrape(
        self,
        query: str,
        limit: int = 25,
        progress_callback: Optional[Callable[[str], Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Mengekstrak data UMKM dari Google Maps berdasarkan query dan limit.
        
        Args:
            query: Kata kunci pencarian (misal: "Cafe Bandung Barat")
            limit: Jumlah target data UMKM (rekomendasi 10 - 50)
            progress_callback: Fungsi async atau sync untuk melaporkan status progres
        """
        results: List[Dict[str, Any]] = []
        encoded_query = urllib.parse.quote_plus(query)
        target_url = f"https://www.google.com/maps/search/{encoded_query}?hl=id"

        async def log_progress(msg: str):
            if progress_callback:
                try:
                    if asyncio.iscoroutinefunction(progress_callback):
                        await progress_callback(msg)
                    else:
                        progress_callback(msg)
                except Exception:
                    pass
            try:
                print(f"[GMapsScraper] {msg}")
            except Exception:
                pass

        await log_progress(f"Membuka browser untuk pencarian: '{query}'...")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-blink-features=AutomationControlled"
                ]
            )
            context = await browser.new_context(
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="id-ID"
            )
            page = await context.new_page()

            try:
                await page.goto(target_url, wait_until="domcontentloaded", timeout=self.timeout_ms)
                await asyncio.sleep(2.5)

                # Cek jika ada dialog persetujuan cookie / accept terms Google
                try:
                    agree_btn = page.locator("button:has-text('Setuju'), button:has-text('Terima semua'), button:has-text('Accept all')").first
                    if await agree_btn.is_visible(timeout=2000):
                        await agree_btn.click()
                        await asyncio.sleep(1.0)
                except Exception:
                    pass

                # Tunggu kontainer hasil pencarian Google Maps
                try:
                    await page.wait_for_selector("a[href*='/maps/place/']", timeout=12000)
                except Exception:
                    await log_progress("Hasil pencarian tidak ditemukan. Query mungkin terlalu spesifik.")
                    await browser.close()
                    return results

                await log_progress("Mulai scrolling daftar hasil...")

                # Scroll feed untuk memuat daftar kartu UMKM
                cards_selector = "a[href*='/maps/place/']"
                previous_count = 0
                max_scroll_attempts = 25
                attempts = 0

                while attempts < max_scroll_attempts:
                    cards = await page.locator(cards_selector).all()
                    current_count = len(cards)

                    if current_count >= limit:
                        await log_progress(f"Tercapai {current_count} calon UMKM dalam feed.")
                        break

                    # Scroll feed ke bawah
                    await page.evaluate("""() => {
                        const feed = document.querySelector("div[role='feed']");
                        if (feed) {
                            feed.scrollTop = feed.scrollHeight;
                        } else {
                            window.scrollBy(0, 1000);
                        }
                    }""")
                    await asyncio.sleep(1.5)

                    # Cek apakah sudah mencapai ujung daftar
                    end_marker = page.locator("text='Anda telah mencapai akhir daftar'")
                    if await end_marker.is_visible():
                        await log_progress("Sudah mencapai akhir daftar Google Maps.")
                        break

                    if current_count == previous_count:
                        attempts += 1
                    else:
                        attempts = 0
                    previous_count = current_count

                # Ambil daftar link tempat yang valid (memiliki aria-label nama tempat)
                card_elements = await page.locator(cards_selector).all()
                valid_cards = []
                for c in card_elements:
                    label = await c.get_attribute("aria-label")
                    if label and label.strip() and label.strip() != "Hasil":
                        valid_cards.append(c)

                total_to_extract = min(len(valid_cards), limit)
                await log_progress(f"Mengekstrak rincian kontak dari {total_to_extract} UMKM...")

                for idx in range(total_to_extract):
                    try:
                        card = valid_cards[idx]
                        
                        # Ambil nama tempat dari aria-label kartu langsung
                        place_name = (await card.get_attribute("aria-label") or "").strip()
                        maps_url = await card.get_attribute("href") or ""
                        if maps_url.startswith("/"):
                            maps_url = f"https://www.google.com{maps_url}"

                        # Scroll elemen ke tampilan agar dapat diklik
                        await card.scroll_into_view_if_needed()
                        await asyncio.sleep(0.4)

                        # Klik kartu untuk membuka panel detail di sebelah kanan
                        await card.click()
                        await asyncio.sleep(1.8)

                        # Verifikasi nama tempat jika detail panel memuat h1 spesifik
                        try:
                            h1_elements = await page.locator("div[role='main'] h1, h1").all()
                            for h in h1_elements:
                                h_text = (await h.inner_text()).strip()
                                if h_text and h_text != "Hasil" and len(h_text) > 1:
                                    place_name = h_text
                                    break
                        except Exception:
                            pass

                        # Ambil Rating & Jumlah Ulasan
                        rating = 0.0
                        reviews_count = 0
                        
                        # Rating dari aria-label bintang
                        try:
                            star_spans = await page.locator("div[role='main'] span[aria-label*='bintang'], span[aria-label*='bintang'], span[aria-label*='star']").all()
                            for s in star_spans:
                                s_label = await s.get_attribute("aria-label") or ""
                                match = re.search(r"([\d]+[.,][\d]+)", s_label)
                                if match:
                                    rating = float(match.group(1).replace(",", "."))
                                    break
                        except Exception:
                            pass

                        # Jumlah ulasan
                        try:
                            rev_spans = await page.locator("div[role='main'] span:has-text('ulasan'), div[role='main'] span:has-text('reviews')").all()
                            for r in rev_spans:
                                r_text = await r.inner_text()
                                match = re.search(r"([\d\.,]+)\s*(?:ulasan|reviews)", r_text, re.IGNORECASE)
                                if match:
                                    raw_num = match.group(1).replace(".", "").replace(",", "")
                                    if raw_num.isdigit():
                                        reviews_count = int(raw_num)
                                        break
                        except Exception:
                            pass

                        # Ambil Kategori Usaha
                        category = ""
                        try:
                            cat_btns = await page.locator("div[role='main'] button[jsaction*='category'], button.DkEaL").all()
                            for cb in cat_btns:
                                c_text = (await cb.inner_text()).strip()
                                if c_text:
                                    category = c_text
                                    break
                        except Exception:
                            pass

                        # Ambil Alamat Lengkap
                        address = ""
                        try:
                            addr_btn = page.locator("button[aria-label*='Alamat:'], button[aria-label*='Address:']").first
                            if await addr_btn.is_visible(timeout=1000):
                                a_label = await addr_btn.get_attribute("aria-label") or ""
                                address = a_label.replace("Alamat:", "").replace("Address:", "").strip()
                        except Exception:
                            pass

                        # Ambil Nomor Telepon
                        phone_raw = ""
                        try:
                            phone_btn = page.locator("button[aria-label*='Telepon:'], button[aria-label*='Phone:'], button[data-tooltip*='nomor telepon']").first
                            if await phone_btn.is_visible(timeout=1000):
                                p_label = await phone_btn.get_attribute("aria-label") or ""
                                phone_raw = p_label.replace("Telepon:", "").replace("Phone:", "").strip()
                        except Exception:
                            pass

                        # Ambil Website / Medsos
                        website = ""
                        try:
                            web_link = page.locator("a[aria-label*='Situs web:'], a[aria-label*='Website:'], a[data-item-id='authority']").first
                            if await web_link.is_visible(timeout=1000):
                                website = await web_link.get_attribute("href") or ""
                        except Exception:
                            pass

                        # Bersihkan nomor telepon & generate WhatsApp direct link
                        phone_info = clean_phone_number(phone_raw)

                        lead_data = {
                            "name": place_name,
                            "category": category,
                            "rating": rating,
                            "reviews_count": reviews_count,
                            "address": address,
                            "phone_raw": phone_raw,
                            "phone_info": phone_info,
                            "website": website,
                            "maps_url": maps_url,
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }

                        results.append(lead_data)
                        phone_display = phone_info['clean'] if phone_info['clean'] else 'Tanpa No'
                        await log_progress(f"[{idx+1}/{total_to_extract}] {place_name} ({category or 'F&B'}) - {phone_display} (⭐{rating} | {reviews_count} rev)")

                    except Exception as item_err:
                        print(f"[Error extracting card {idx}]: {item_err}")
                        continue

            except Exception as e:
                await log_progress(f"Terjadi kesalahan saat scraping: {str(e)}")
            finally:
                await context.close()
                await browser.close()

        await log_progress(f"Selesai! Berhasil mengumpulkan {len(results)} data UMKM.")
        return results
