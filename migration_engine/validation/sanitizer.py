"""
PII Masking & Data Sanitization Module (Milestone 17)
Ensures sensitive banking fields (DOB, Phone, Email, Account Numbers)
are masked before diagnostic logging or external output.
"""
import re

def mask_email(email: str) -> str:
    if not email or "@" not in email:
        return email or ""
    parts = email.split("@")
    name, domain = parts[0], parts[1]
    if len(name) <= 2:
        masked_name = name[0] + "*"
    else:
        masked_name = name[0] + "*" * (len(name) - 2) + name[-1]
    return f"{masked_name}@{domain}"

def mask_phone(phone: str) -> str:
    if not phone:
        return ""
    digits = re.sub(r'\D', '', phone)
    if len(digits) >= 4:
        return "*" * (len(digits) - 4) + digits[-4:]
    return "****"

def mask_dob(dob: str) -> str:
    if not dob:
        return ""
    # Mask year/month, e.g. 1985-05-15 -> XXXX-XX-15
    parts = dob.split("-")
    if len(parts) == 3:
        return f"XXXX-XX-{parts[2]}"
    return "XXXX-XX-XX"
