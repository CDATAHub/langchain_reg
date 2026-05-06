import re


PHONE_PATTERN = re.compile(r"(?<!\d)(1\d{2})\d{4}(\d{4})(?!\d)")
ID_CARD_PATTERN = re.compile(r"(?<!\w)(\d{6})\d{8}(\w{4})(?!\w)")
POLICY_PATTERN = re.compile(r"(?i)(policy[_-]?no\s*[:：]?\s*)([A-Z0-9]{6,})")


def mask_pii(text: str) -> str:
    if not text:
        return text

    masked = PHONE_PATTERN.sub(r"\1****\2", text)
    masked = ID_CARD_PATTERN.sub(r"\1********\2", masked)
    masked = POLICY_PATTERN.sub(r"\1****", masked)
    return masked


def summarize_text(text: str, max_length: int = 200) -> str:
    masked = mask_pii(text).strip()
    if len(masked) <= max_length:
        return masked
    return masked[: max_length - 3] + "..."
