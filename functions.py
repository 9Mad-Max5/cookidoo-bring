from fractions import Fraction
from typing import Optional
import re

UNICODE_FRACTIONS = {
    "¼": "1/4",
    "½": "1/2",
    "¾": "3/4",
    "⅓": "1/3",
    "⅔": "2/3",
    "⅛": "1/8",
    "⅜": "3/8",
    "⅝": "5/8",
    "⅞": "7/8",
}

def parse_amount_and_unit(s: str) -> tuple[Optional[float], Optional[str]]:
    s = s.strip()

    # Sonderfall: Ganze Zeile besteht nur aus "Prise", "n. B.", etc.
    if not re.search(r"[\d¼½¾⅓⅔⅛⅜⅝⅞]", s):
        return None, s  # keine Zahl enthalten → ganze Zeile = Einheit

    # Ersetze Unicode-Brüche durch ASCII-Brüche
    for unicode_char, ascii_frac in UNICODE_FRACTIONS.items():
        if unicode_char in s:
            s = s.replace(unicode_char, ascii_frac)
            break

    parts = s.split(maxsplit=1)
    if not parts:
        return None, None

    # Versuche ersten Teil als Bruch zu interpretieren
    amount = parts[0]
    # try:
    #     amount = float(Fraction(parts[0].replace(",", ".")))
    # except Exception:
    #     amount = None

    # Zweiter Teil ist optional die Einheit
    unit = parts[1].strip() if len(parts) > 1 else None

    return amount, unit
