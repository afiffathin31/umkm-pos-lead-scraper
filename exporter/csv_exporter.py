import os
import re
from datetime import datetime
from typing import List, Dict, Any
import pandas as pd

def calculate_pos_prospect(rating: float, reviews: int) -> str:
    """Menentukan tingkat prioritas prospek POS berdasarkan ulasan & rating."""
    if reviews >= 100 and rating >= 4.0:
        return "Prioritas Tinggi (Usaha Ramai & Butuh POS Cepat)"
    elif reviews >= 30:
        return "Prioritas Sedang (Potensial Upgrade POS)"
    elif reviews > 0:
        return "Prioritas Normal (UMKM Berkembang)"
    else:
        return "Baru Terdaftar / Belum Ada Ulasan"

def export_to_csv(data: List[Dict[str, Any]], query: str, output_dir: str = "exports") -> str:
    """
    Mengekspor list data UMKM ke file CSV dengan format ramah Excel (UTF-8 with BOM).
    
    Returns:
        str: Absolute file path dari CSV yang dihasilkan.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Format query untuk nama file yang aman
    safe_query = re.sub(r"[^\w\s-]", "", query).strip().lower()
    safe_query = re.sub(r"[-\s]+", "_", safe_query)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"leads_{safe_query}_{timestamp}.csv"
    filepath = os.path.abspath(os.path.join(output_dir, filename))
    
    rows = []
    for idx, item in enumerate(data, start=1):
        phone_info = item.get("phone_info", {})
        rating = float(item.get("rating", 0) or 0)
        reviews = int(item.get("reviews_count", 0) or 0)
        
        is_mobile = phone_info.get("is_mobile", False)
        clean_phone = phone_info.get("clean", "")
        
        if is_mobile:
            contact_type = "WhatsApp (Seluler)"
        elif clean_phone:
            contact_type = "Telepon Kabel / Kantor"
        else:
            contact_type = "Belum Ada Nomor"
            
        prospect_score = calculate_pos_prospect(rating, reviews)
        
        # Format nomor telepon dengan petik tunggal ' agar Excel tetap memperlakukan sebagai teks
        phone_for_excel = f"'{clean_phone}" if clean_phone else ""
        
        rows.append({
            "No": idx,
            "Nama UMKM": item.get("name", ""),
            "Kategori": item.get("category", ""),
            "Status Prospek POS": prospect_score,
            "Rating": rating if rating > 0 else "-",
            "Jumlah Ulasan": reviews,
            "Tipe Kontak": contact_type,
            "Nomor Telepon": phone_for_excel,
            "Link Chat WhatsApp": phone_info.get("wa_link", ""),
            "Alamat Lengkap": item.get("address", ""),
            "Website / Medsos": item.get("website", ""),
            "Link Google Maps": item.get("maps_url", ""),
            "Waktu Scraping": item.get("scraped_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        })
        
    df = pd.DataFrame(rows)
    # Gunakan encoding 'utf-8-sig' agar Excel di Windows membaca karakter & BOM dengan sempurna
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    return filepath
