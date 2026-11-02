import pytest
from utils.phone_cleaner import clean_phone_number

def test_mobile_with_leading_zero():
    res = clean_phone_number("0812-3456-7890")
    assert res["is_mobile"] is True
    assert res["clean"] == "6281234567890"
    assert res["wa_link"] == "https://wa.me/6281234567890"
    assert "+62 812-3456-7890" in res["formatted"]

def test_mobile_with_country_code():
    res = clean_phone_number("+62 813 9988 7766")
    assert res["is_mobile"] is True
    assert res["clean"] == "6281399887766"
    assert res["wa_link"] == "https://wa.me/6281399887766"

def test_landline_bandung():
    res = clean_phone_number("(022) 7201234")
    assert res["is_mobile"] is False
    assert res["wa_link"] == ""
    assert res["clean"] == "0227201234"

def test_landline_with_country_code():
    res = clean_phone_number("+62 21 5554321")
    assert res["is_mobile"] is False
    assert res["wa_link"] == ""

def test_empty_or_none():
    res1 = clean_phone_number("")
    assert res1["clean"] == ""
    assert res1["wa_link"] == ""
    
    res2 = clean_phone_number(None)
    assert res2["clean"] == ""
    assert res2["wa_link"] == ""
