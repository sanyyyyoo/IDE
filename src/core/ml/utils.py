# src/core/ml/utils.py

import re
import phonenumbers

def normalize_phone(text: str) -> str:
    if not text:
        return ""
    try:
        cleaned = re.sub(r"[^\d\+]", "", text)
        if not cleaned.startswith("+") and len(cleaned)==10:
            cleaned = "+91"+cleaned
        parsed = phonenumbers.parse(cleaned,"IN")
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed,phonenumbers.PhoneNumberFormat.E164)
        return ""
    except:  # noqa: E722
        return ""

def normalize_address(text: str) -> str:
    return text.strip() if text else ""

def normalize_name(text: str) -> str:
    return text.strip() if text else ""

def normalize_category(text: str) -> str:
    return text.strip().lower() if text else ""
