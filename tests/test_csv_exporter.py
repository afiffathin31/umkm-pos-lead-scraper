import os
import pandas as pd
from exporter.csv_exporter import export_to_csv, calculate_pos_prospect
from utils.phone_cleaner import clean_phone_number

def test_pos_prospect_scoring():
    assert "Tinggi" in calculate_pos_prospect(4.5, 120)
    assert "Sedang" in calculate_pos_prospect(4.2, 45)
    assert "Normal" in calculate_pos_prospect(3.8, 10)
    assert "Baru" in calculate_pos_prospect(0, 0)

import tempfile

def test_export_to_csv():
    with tempfile.TemporaryDirectory() as tmp_dir:
        dummy_data = [
            {
                "name": "Kopi Toko Djawa",
                "category": "Kedai Kopi",
                "rating": 4.6,
                "reviews_count": 520,
                "address": "Jl. Braga No.81, Bandung",
                "phone_raw": "0812-9988-7766",
                "phone_info": clean_phone_number("0812-9988-7766"),
                "website": "https://instagram.com/kopitokodjawa",
                "maps_url": "https://maps.google.com/?cid=12345",
                "scraped_at": "2026-09-22 13:00:00"
            },
            {
                "name": "Bakso Solo Mas No",
                "category": "Restoran Bakso",
                "rating": 4.3,
                "reviews_count": 45,
                "address": "Jl. Riau No.12, Bandung",
                "phone_raw": "(022) 7201234",
                "phone_info": clean_phone_number("(022) 7201234"),
                "website": "",
                "maps_url": "https://maps.google.com/?cid=67890",
                "scraped_at": "2026-09-22 13:00:00"
            }
        ]
        
        csv_path = export_to_csv(dummy_data, query="Cafe Bandung", output_dir=tmp_dir)
        assert os.path.exists(csv_path)
        
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
        assert len(df) == 2
        assert "Kopi Toko Djawa" in df["Nama UMKM"].values
        assert "https://wa.me/6281299887766" in df["Link Chat WhatsApp"].values
        assert "WhatsApp (Seluler)" in df["Tipe Kontak"].values
        assert "Telepon Kabel / Kantor" in df["Tipe Kontak"].values

