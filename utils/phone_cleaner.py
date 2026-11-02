import re
from typing import Dict, Any

def clean_phone_number(raw_phone: str) -> Dict[str, Any]:
    """
    Membersihkan dan menormalisasi nomor telepon Indonesia dari Google Maps.
    
    Returns dictionary:
        - raw: nomor asli
        - clean: nomor standar (628xxx untuk HP, 021xxx untuk telepon kabel)
        - formatted: format baca rapi (+62 8xx-xxxx-xxxx)
        - is_mobile: bool apakah nomor seluler (WhatsAppable)
        - wa_link: link langsung wa.me jika nomor seluler
    """
    if not raw_phone or not isinstance(raw_phone, str):
        return {
            "raw": "",
            "clean": "",
            "formatted": "",
            "is_mobile": False,
            "wa_link": ""
        }
    
    # Ambil hanya digit angka dan tanda plus awal
    has_plus = raw_phone.strip().startswith("+")
    digits_only = re.sub(r"[^\d]", "", raw_phone)
    
    if not digits_only:
        return {
            "raw": raw_phone.strip(),
            "clean": "",
            "formatted": "",
            "is_mobile": False,
            "wa_link": ""
        }
    
    # Normalisasi nomor seluler Indonesia
    # Contoh kasus:
    # 08123456789 -> 628123456789
    # +628123456789 -> 628123456789
    # 628123456789 -> 628123456789
    clean_num = digits_only
    is_mobile = False
    
    if clean_num.startswith("08"):
        clean_num = "62" + clean_num[1:]
        is_mobile = True
    elif clean_num.startswith("628"):
        is_mobile = True
    elif clean_num.startswith("8") and len(clean_num) >= 9:
        clean_num = "62" + clean_num
        is_mobile = True
    elif clean_num.startswith("0"):
        # Telepon PSTN kabel kantor / rumah (021, 022, 031, dll)
        is_mobile = False
    elif clean_num.startswith("62") and not clean_num.startswith("628"):
        # Telepon kabel format internasional (+62 21 ...)
        is_mobile = False
        
    # Validasi panjang nomor HP Indonesia (biasanya 10 - 15 digit total termasuk prefix 62)
    if is_mobile and 10 <= len(clean_num) <= 15:
        wa_link = f"https://wa.me/{clean_num}"
        # Format keterbacaan: +62 812-3456-7890
        sub_num = clean_num[2:]
        if len(sub_num) >= 7:
            prefix = sub_num[:3]
            mid = sub_num[3:7]
            rest = sub_num[7:]
            formatted = f"+62 {prefix}-{mid}-{rest}" if rest else f"+62 {prefix}-{mid}"
        else:
            formatted = f"+{clean_num}"
    else:
        is_mobile = False
        wa_link = ""
        # Untuk nomor rumah/kantor jika diawali 62 diubah kembali ke 0 untuk format lokal (misal 021-xxxx)
        if clean_num.startswith("62") and len(clean_num) > 3:
            local_format = "0" + clean_num[2:]
            formatted = local_format
        else:
            formatted = clean_num

    return {
        "raw": raw_phone.strip(),
        "clean": clean_num,
        "formatted": formatted,
        "is_mobile": is_mobile,
        "wa_link": wa_link
    }
