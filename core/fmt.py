"""Number formatting according to the active language."""
from __future__ import annotations

import math

from .i18n import get_lang

SYMBOL = {"EUR": "€", "USD": "$", "GBP": "£", "BRL": "R$", "AOA": "Kz", "MZN": "MT", "CVE": "CVE", "CHF": "CHF"}


def num(x, dec: int = 0) -> str:
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "—"
    if math.isnan(x) or math.isinf(x):
        return "—"
    s = f"{x:,.{dec}f}"
    if get_lang() == "pt":
        s = s.replace(",", " ").replace(".", ",")
    return s


def money(x, cur: str = "EUR", dec: int = 0) -> str:
    s = num(x, dec)
    if s == "—":
        return s
    sym = SYMBOL.get(cur, cur)
    return f"{s} {sym}" if get_lang() == "pt" or sym in ("€", "Kz", "MT", "CVE", "CHF") else f"{sym}{s}"


def pct(x, dec: int = 1) -> str:
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "—"
    if math.isnan(x) or math.isinf(x):
        return "—"
    return num(x * 100, dec) + "%"


def unit_label(unit: str, plural: bool = True) -> str:
    pt = {"days": "dias", "weeks": "semanas", "months": "meses"}
    return pt.get(unit, unit) if get_lang() == "pt" else unit


def d(date_obj) -> str:
    try:
        return date_obj.strftime("%d/%m/%Y") if get_lang() == "pt" else date_obj.strftime("%Y-%m-%d")
    except Exception:
        return str(date_obj)
