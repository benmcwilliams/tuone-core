import re
import sys, os
import pandas as pd
import pycountry
import unicodedata
import pandas as pd
from currency_converter import CurrencyConverter

root = os.path.abspath(os.path.join(os.getcwd(), ".."))
if root not in sys.path:
    sys.path.append(root)

from numerizer import numerize
from word2number import w2n
from reconcile.src import id_date_dict
from currency_symbols import CurrencySymbols  # pip install currency-symbols
from src.id_date_dict import get_article_id_to_date_map
from src.split_investments import _is_missing, _as_iter, multiply_vals, distribute_vehicle_battery_split

from forex_python.converter import CurrencyRates

# ======= Currency metadata =======
def build_currency_list():
    """Return list of tuples (iso, symbol, name)."""
    out = []
    for cur in pycountry.currencies:
        iso = cur.alpha_3
        name = cur.name
        symbol = CurrencySymbols.get_symbol(iso) or ""
        out.append((iso, symbol, name))
    return out

currency_list = build_currency_list()
ALL_ISOS = {iso for iso, _, _ in currency_list}

# Common name aliases (extend as needed)
NAME_ALIASES = {
    "dollar": "USD", "dollars": "USD", "buck": "USD", "bucks": "USD",
    "euro": "EUR", "euros": "EUR",
    "pound": "GBP", "pounds": "GBP", "sterling": "GBP", "quid": "GBP",
    "yen": "JPY", "yens": "JPY",
    "yuan": "CNY", "renminbi": "CNY", "rmb": "CNY",
    "rupee": "INR", "rupees": "INR",
    "won": "KRW",
    "franc": "CHF", "francs": "CHF",
    "lira": "TRY", "lire": "TRY",
    "dirham": "AED", "riyal": "SAR", "ringgit": "MYR", "baht": "THB",
    "peso": "MXN", "pesos": "MXN",
    "kronor": "SEK", "krona": "SEK", "krone": "NOK", "kroner": "NOK",
    "zlotys": "PLN", "zloty": "PLN",
    "crowns": "CZK", "koruna": "CZK",
}

# Unambiguous symbol mapping (leave "$" out—it's ambiguous)
SYMBOL_TO_ISO = {
    "€": "EUR", "£": "GBP", "₤": "GBP", "¥": "JPY", "₩": "KRW", "₽": "RUB",
    "₹": "INR", "₺": "TRY", "₫": "VND", "₪": "ILS", "₦": "NGN", "₱": "PHP",
    "₲": "PYG", "₴": "UAH", "₡": "CRC", "₭": "LAK", "₸": "KZT",
}

# Build NAME_TO_ISO from pycountry + aliases (word forms)
NAME_TO_ISO = dict(NAME_ALIASES)
for iso, sym, name in currency_list:
    if name:
        base = name.strip().lower()
        if base:
            NAME_TO_ISO[base] = iso
            if not base.endswith("s"):
                NAME_TO_ISO[base + "s"] = iso  # naive plural

# --- Nordic disambiguation + krona/krone handling ---
SCANDI_ADJ_TO_ISO = {
    "swedish": "SEK",
    "norwegian": "NOK",
    "danish": "DKK",
    "icelandic": "ISK",
}

# --- Country -> currency helpers (extend as needed) ---
COUNTRY_CURRENCY_TOKENS = {
    # canonical token : ISO
    "us": "USD", "u.s.": "USD", "u.s": "USD",
    "usa": "USD", "u.s.a.": "USD",
    "united states": "USD",
    "uk": "GBP", "u.k.": "GBP", "great britain": "GBP", "united kingdom": "GBP",  # optional
}

# Tokens we consider only when they appear as standalone words or right before $
COUNTRY_TOKEN_RE = re.compile(
    r"\b(u\.?s\.?a?\.?|united states|u\.?k\.?|united kingdom|great britain)\b",
    re.IGNORECASE
)

# Multi-character "symbols" like "US$"
MULTI_SYMBOL_TO_ISO = {
    "us$": "USD",
    "u.s.$": "USD",
    "u$s": "USD",   # very rare, but cheap to support
    # Add others if you ever need, e.g., "C$" (CAD), "A$" (AUD), "NZ$" (NZD)
    "c$": "CAD",
    "a$": "AUD",
    "nz$": "NZD",
    "€": "EUR"
}


# Recognize krona/kronor/krone/kroner (incl. accented forms)
KRON_WORDS_RE = re.compile(r"\b(krona|kronor|krone|kroner|krónur|króna)\b", re.IGNORECASE)
KRON_ROOT_RE  = re.compile(r"\bkron[a-záú]*\b", re.IGNORECASE)

# Build precise word-boundary name matcher from NAME_TO_ISO (longest first)
NAMES_ORDERED = sorted(NAME_TO_ISO.keys(), key=len, reverse=True)
NAME_TOKEN_RE = re.compile(r"\b(?:%s)\b" % "|".join(re.escape(n) for n in NAMES_ORDERED), re.IGNORECASE)

# Regex for token removal (names, isos, symbols)
names_sorted = sorted(NAME_TO_ISO.keys(), key=len, reverse=True)
name_alt = "|".join(re.escape(n) for n in names_sorted)
iso_alt  = r"[A-Za-z]{3}"  # validated afterwards
sym_alt  = "|".join(re.escape(s) for s in SYMBOL_TO_ISO.keys())
CURRENCY_TOKEN_RE = re.compile(
    rf"(?P<iso>\b{iso_alt}\b)|(?P<name>\b(?:{name_alt})\b)|(?P<sym>(?:{sym_alt}))",
    flags=re.IGNORECASE
)

def _strip_accents(s: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))

def _normalize_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()

def detect_currency_iso(text: str) -> str | None:
    if not isinstance(text, str) or not text.strip():
        return None
    t = text
    t_fold = _strip_accents(t).lower()

    # 0) Multi-character "symbols" like "US$"
    for msym, iso in MULTI_SYMBOL_TO_ISO.items():
        if msym in t_fold:
            return iso


    # 1) ISO stuck to number, e.g., "PLN70bn", "usd2.5m"
    for m in re.finditer(r'(?<![A-Za-z])([A-Za-z]{3})(?=\d)', t):
        cand_u = m.group(1).upper()
        if cand_u in ALL_ISOS:
            return cand_u

    # 2) explicit ISO tokens (any case)
    for m in re.finditer(r"\b([A-Za-z]{3})\b", t):
        cand_u = m.group(1).upper()
        if cand_u in ALL_ISOS:
            return cand_u

    # 3) disambiguate Nordic "kron*" by adjective
    if KRON_ROOT_RE.search(t_fold):
        for adj, iso in SCANDI_ADJ_TO_ISO.items():
            if re.search(rf"\b{adj}\b", t_fold):
                return iso

    # 4) currency names with strict word boundaries
    m = NAME_TOKEN_RE.search(t_fold)
    if m:
        iso = NAME_TO_ISO.get(m.group(0).lower())
        if iso:
            return iso

    # 5) country tokens that imply a currency (e.g., "US", "USA") near number or dollar
    #    We only trigger if a number or "$" appears within a short window to reduce false positives.
    if COUNTRY_TOKEN_RE.search(t_fold):
        if re.search(r"\$|\d", t_fold):  # cheap proximity heuristic
            # pick the first matching token and map it
            for match in COUNTRY_TOKEN_RE.finditer(t_fold):
                tok = match.group(0).lower().replace(" ", "")
                # normalize a few variants
                tok = tok.replace(".", "")
                if tok in ("us", "usa", "unitedstates"):
                    return "USD"
                if tok in ("uk", "unitedkingdom", "greatbritain"):
                    return "GBP"

    # 6) unambiguous single-char symbols
    for sym, iso in SYMBOL_TO_ISO.items():
        if sym in t:
            return iso

    # 7) ambiguous "$" — light heuristic
    if "$" in t:
        if "peso" in t_fold or "pesos" in t_fold:
            return "MXN"
        # If a country token was seen, prefer its currency
        if COUNTRY_TOKEN_RE.search(t_fold):
            return "USD"  # currently only US supported above
        return "USD"

    return None


#To drop currency tokens from text - drop in the final version
def remove_currency_tokens(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return text
    cleaned = text

    # Drop multi-char currency "symbols" like "US$"
    for msym in MULTI_SYMBOL_TO_ISO.keys():
        cleaned = re.sub(re.escape(msym), " ", cleaned, flags=re.IGNORECASE)

    # Drop standard currency tokens (names, isos, one-char symbols) — but VALIDATE ISOs
    def _drop_if_currency(m: re.Match) -> str:
        iso  = m.group("iso")
        name = m.group("name")
        sym  = m.group("sym")

        if sym:  # unambiguous symbols like €, £, ¥ ...
            return " "
        if name:  # names come from NAME_TO_ISO, safe to drop
            return " "
        if iso:
            cand = iso.upper()
            return " " if cand in ALL_ISOS else m.group(0)  # keep non-ISO 3-letter words!
        return m.group(0)

    cleaned = CURRENCY_TOKEN_RE.sub(_drop_if_currency, cleaned)

    # Remove ISO stuck to number, e.g. "pln70bn" -> " 70bn" (validate again)
    def _repl_iso_stuck(m: re.Match) -> str:
        cand_u = m.group(1).upper()
        return " " if cand_u in ALL_ISOS else m.group(0)
    cleaned = re.sub(r'(?<![A-Za-z])([A-Za-z]{3})(?=\d)', _repl_iso_stuck, cleaned)

    # Also drop krona/kronor/krone/kroner tokens
    cleaned = KRON_WORDS_RE.sub(" ", cleaned)

    # Drop ambiguous dollar symbol
    cleaned = cleaned.replace("$", " ")

    # Drop country tokens that imply currency (US, USA, U.S., etc.)
    cleaned = COUNTRY_TOKEN_RE.sub(" ", cleaned)

    return _normalize_spaces(cleaned)


# ======= Numeric parsing bits =======
SCALE_MAP = {
    "thousand": 1e3, "thousands": 1e3, "k": 1e3, "K": 1e3, "kilo": 1e3, "kilos": 1e3,
    "million": 1e6, "millions": 1e6, "m": 1e6, "M": 1e6, "mn": 1e6, "MN": 1e6, "mln": 1e6, "MLN": 1e6,
    "billion": 1e9, "billions": 1e9, "b": 1e9, "B": 1e9, "bn": 1e9, "BN": 1e9, "bln": 1e9, "BLN": 1e9,
    "trillion": 1e12, "trillions": 1e12, "trn": 1e12, "TRN": 1e12
}

DIGIT_WORD_MAP = {
    "single": 1, "double": 2, "triple": 3, "quadruple": 4, "quad": 4,
    "quintuple": 5, "sextuple": 6, "septuple": 7, "octuple": 8, "nonuple": 9,
}

def _parse_digit_count(token: str):
    t = token.lower()
    if t.isdigit():
        return int(t)
    if t in DIGIT_WORD_MAP:
        return DIGIT_WORD_MAP[t]
    try:
        return w2n.word_to_num(t)
    except Exception:
        return None

def _to_float(s: str) -> float:
    s = s.strip().replace('\u00a0', ' ')
    has_comma = ',' in s
    has_dot = '.' in s
    if has_comma and has_dot:
        if s.rfind(',') > s.rfind('.'):
            s = s.replace('.', '').replace(',', '.')
        else:
            s = s.replace(',', '')
    elif has_comma:
        if re.match(r'^\d{1,3}(,\d{3})+$', s):
            s = s.replace(',', '')
        else:
            s = s.replace(',', '.')
    return float(s.replace(' ', ''))

def _join_currency_rest(*parts):
    return " ".join(p for p in (p.strip() for p in parts) if p)


SCALE_TOKEN = r"(thousand|million|billion|trillion|k|m|mn|mln|b|bn|bln)"

# Put this near your other globals
APPROX_PREFIXES = ("about", "around", "approximately", "approx", "nearly", "almost", "close to")
UPPER_BOUND_PREFIXES = ("up to", "less than", "under")
LOWER_BOUND_PREFIXES = ("more than", "over", "well over")

PREFIX_RE = re.compile(
    r"^(?P<prefix>up to|less than|under|more than|over|well over|about|around|approximately|approx|nearly|almost|close to)\b\s*",
    re.IGNORECASE
)

def _wrap_inequality(prefix: str | None, raw_value, amount_scalar, remaining):
    # if no prefix or already a range, pass through
    if not prefix or isinstance(raw_value, list):
        return raw_value, amount_scalar, remaining
    p = prefix.lower()
    if p in APPROX_PREFIXES:
        return raw_value, amount_scalar, remaining  # keep single value
    if p in UPPER_BOUND_PREFIXES:
        return [None, raw_value], amount_scalar, remaining
    if p in LOWER_BOUND_PREFIXES:
        return [raw_value, None], amount_scalar, remaining
    return raw_value, amount_scalar, remaining

# CHECK THIS - I HAD TO ADD TO EXECUTE CODE
APPROX_PREFIX = "about"

REGEX_PATTERNS = {
    "range_numeric": r"^([0-9,.]+)\s*(?:to|-|–|—)\s*([0-9,.]+)\s+(.*)",
    "word_range_scale": (
        r"^([a-z]+)\s*(?:to|-|–|—)\s*([a-z]+)\s+" + SCALE_TOKEN +
        r"\b\s*(.*)"
    ),
    "range_with_scale": (
        r"^([0-9.,]+)\s+" + SCALE_TOKEN + r"\s*"
        r"(?:to|-|–|—)\s*([0-9.,]+)\s+" + SCALE_TOKEN +
        r"\s*(.*)"
    ),
    "digit_scale": r"^([a-z0-9]+)(?:-|\s*)digit\s+(thousand|million|billion|trillion)\b\s*(.*)",
    "mixed_fraction_scaled": r"^([a-z0-9\s-]+?)\s+and a half\s+(thousand|million|billion|trillion)\b\s*(.*)",
    "unified_amount": (
        r"^(?:" + APPROX_PREFIX + r")?"
        r"([0-9.,]+|[a-z\s-]+?)"
        r"(?:\s+" + SCALE_TOKEN + r")?"
        r"\b\s*(.*)"
    ),
    "num_with_scale_stuck": r"^([0-9.,]+)\s*([A-Za-z]+)\b\s*(.*)",
    "plain_numeric_unit": r"^([0-9,.]+)\s*([A-Za-z/].*)",
    "fallback": r"^([0-9,.]+)\s*(thousand|million|billion|trillion)?\b\s*(.*)",
}

# --- Pre-clean helpers ---

# Remove (...) blocks completely (and the parentheses themselves)
PARENS_RE = re.compile(r"\([^)]*\)")
def _drop_parentheses(text: str) -> str:
    if not isinstance(text, str):
        return text
    return _normalize_spaces(PARENS_RE.sub(" ", text))

# Replace hyphen / en dash / em dash with a space UNLESS it is between two digits (keeps numeric ranges)
DASH_CHARS = r"-–—"
NOT_BETWEEN_DIGITS_DASH_RE = re.compile(r"(?<!\d)[-–—]|[-–—](?!\d)")
def _soft_remove_dashes(text: str) -> str:
    if not isinstance(text, str):
        return text
    # First unify all dash-like chars to a single '-' to simplify, then remove where safe
    unified = re.sub(f"[{DASH_CHARS}]", "-", text)
    cleaned = NOT_BETWEEN_DIGITS_DASH_RE.sub(" ", unified)
    return _normalize_spaces(cleaned)

def _preclean_investment_text(text: str) -> str:
    """Parentheses removal + dash cleanup + space normalization."""
    if not isinstance(text, str):
        return ""
    t = _drop_parentheses(text)
    t = _soft_remove_dashes(t)
    return _normalize_spaces(t)


# ======= Amount parser (uses cleaned text) =======
def parse_amount_from_text(text_clean: str):
    """Return (raw_value, amount_scalar, remaining) from already currency-cleaned text."""
    if not isinstance(text_clean, str):
        return None, None, None
    text = text_clean.strip()

    # --- 0) detect & strip leading modifier once (for inequalities/approx) ---
    m_pref = PREFIX_RE.match(text)
    prefix = None
    if m_pref:
        prefix = m_pref.group("prefix")
        text = text[m_pref.end():].lstrip()

    # --- 1) true ranges: return as [lo, hi] + scalar (no inequality wrapping) ---
    m = re.match(REGEX_PATTERNS["word_range_scale"], text, re.IGNORECASE)
    if m:
        try:
            word1, word2, scale_token, remaining = m.groups()
            v1 = w2n.word_to_num(word1); v2 = w2n.word_to_num(word2)
            scl = SCALE_MAP.get(scale_token.lower())
            if scl:
                return [v1, v2], scl, remaining
        except Exception:
            pass

    m = re.match(REGEX_PATTERNS["range_numeric"], text, re.IGNORECASE)
    if m:
        try:
            v1 = _to_float(m.group(1)); v2 = _to_float(m.group(2))
            remaining = m.group(3).lstrip()
            m_scale = re.match(rf"^(?P<scale>{SCALE_TOKEN})\b\s*(?P<rest>.*)", remaining, re.IGNORECASE)
            if m_scale:
                scl = SCALE_MAP.get(m_scale.group("scale").lower())
                if scl:
                    remaining = m_scale.group("rest").strip()
                    return [v1, v2], scl, remaining
            return [v1, v2], None, remaining
        except Exception:
            pass

    m = re.match(REGEX_PATTERNS["range_with_scale"], text, re.IGNORECASE)
    if m:
        try:
            v1s, s1, v2s, s2, remaining = m.groups()
            scl1 = SCALE_MAP.get(s1.lower()); scl2 = SCALE_MAP.get(s2.lower())
            if scl1 and scl2 and scl1 == scl2:
                v1 = _to_float(v1s); v2 = _to_float(v2s)
                return [v1, v2], scl1, remaining
        except Exception:
            pass

    m = re.match(REGEX_PATTERNS["digit_scale"], text, re.IGNORECASE)
    if m:
        try:
            token, scale_token, remaining = m.groups()
            digits = _parse_digit_count(token)
            scl = SCALE_MAP.get(scale_token.lower())
            if scl and digits and digits >= 2:
                low = (10 ** (digits - 1)) * scl
                high = (10 ** digits - 1) * scl
                return [low, high], None, remaining
        except Exception:
            pass

    # --- 2) single-amount patterns: compute value+scalar, then apply inequality wrapper ---
    m = re.match(REGEX_PATTERNS["num_with_scale_stuck"], text, re.IGNORECASE)
    if m:
        try:
            num_str, suffix, remaining = m.groups()
            scl = SCALE_MAP.get(suffix.lower())
            if scl:
                value = _to_float(num_str)
                return _wrap_inequality(prefix, value, scl, remaining)
        except Exception:
            pass

    m = re.match(REGEX_PATTERNS["mixed_fraction_scaled"], text, re.IGNORECASE)
    if m:
        try:
            whole, scale_str, remaining = m.groups()
            scl = SCALE_MAP.get(scale_str.lower())
            if scl:
                w = float(whole) if whole.isdigit() else w2n.word_to_num(whole)
                return _wrap_inequality(prefix, w + 0.5, scl, remaining)
        except Exception:
            pass

    m = re.match(REGEX_PATTERNS["unified_amount"], text, re.IGNORECASE)
    if m:
        try:
            amount_str, scale_token, remaining = m.groups()
            if re.search(r"\bdigit\b", amount_str, flags=re.IGNORECASE):
                raise ValueError()
            if re.fullmatch(r"[0-9.,]+", amount_str.strip()):
                value = _to_float(amount_str)
            else:
                value = w2n.word_to_num(amount_str.strip())
            scl = SCALE_MAP.get(scale_token.lower()) if scale_token else None
            return _wrap_inequality(prefix, value, scl, remaining)
        except Exception:
            pass


    m = re.match(REGEX_PATTERNS["plain_numeric_unit"], text, re.IGNORECASE)
    if m:
        try:
            value = _to_float(m.group(1))
            remaining = m.group(2).strip()
            return _wrap_inequality(prefix, value, None, remaining)
        except Exception:
            pass

    # numerize + fallback
    try:
        numerized = numerize(text.lower())
        m = re.match(REGEX_PATTERNS["fallback"], numerized, re.IGNORECASE)
        if m:
            value = _to_float(m.group(1))
            scl = SCALE_MAP.get((m.group(2) or "").lower()) if m.group(2) else None
            remaining = m.group(3).strip()
            return _wrap_inequality(prefix, value, scl, remaining)
    except Exception:
        pass

    return None, None, text

# reconcile/src/capacity_helpers.py

import math
import pandas as pd

# ======= Year + FX conversions (simple, latest rates) =======
# ======= Year + ECB FX conversions (simple, date-aware) =======

# build once; fallbacks let it use nearest available ECB rate if exact date missing
_CCY = CurrencyConverter(
    fallback_on_missing_rate=True,
    fallback_on_wrong_date=True
)

def _map_amount_shape_preserving(value, fn):
    """Apply fn to scalar or list/tuple, preserving shape and None values."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (list, tuple)):
        out = []
        for v in value:
            if v is None or (isinstance(v, float) and pd.isna(v)):
                out.append(None)
            else:
                try:
                    out.append(fn(v))
                except Exception:
                    out.append(None)
        return out
    try:
        return fn(value)
    except Exception:
        return None

# ======= Year + ECB FX conversions (simple, date-aware) =======
import pandas as pd
from currency_converter import CurrencyConverter

# build once; fallback lets it use nearest available ECB rate if exact date missing
_CCY = CurrencyConverter(
    fallback_on_missing_rate=True,
    fallback_on_wrong_date=True
)

def _map_amount_shape_preserving(value, fn):
    """Apply fn to scalar or list/tuple, preserving shape and None values."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (list, tuple)):
        out = []
        for v in value:
            if v is None or (isinstance(v, float) and pd.isna(v)):
                out.append(None)
            else:
                try:
                    out.append(fn(v))
                except Exception:
                    out.append(None)
        return out
    try:
        return fn(value)
    except Exception:
        return None

def add_year_and_fx_currencyconverter(
    df: pd.DataFrame,
    date_col: str = "date",
    currency_col: str = "currency_iso",
    amount_col: str = "amount_value"
) -> pd.DataFrame:
    """
    Adds:
      - 'year' from `date_col`
      - 'amount_EUR' and 'amount_USD' using ECB historical rates (currencyconverter).
    """
    if df.empty:
        df["year"] = pd.Series(dtype="Int64")
        df["amount_EUR"] = pd.Series(dtype="object")
        df["amount_USD"] = pd.Series(dtype="object")
        return df

    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col], errors="coerce")
    out["year"] = out[date_col].dt.year.astype("Int64")

    def _convert_row(row):
        cur = (row.get(currency_col) or "").upper()
        val = row.get(amount_col)
        dt  = row.get(date_col)
        on_date = dt.date() if pd.notna(dt) else None

        def to_eur(x):
            if cur == "EUR":
                return x
            try:
                return _CCY.convert(x, cur, "EUR", date=on_date)
            except Exception:
                return None

        def eur_to_usd(x):
            try:
                return _CCY.convert(x, "EUR", "USD", date=on_date)
            except Exception:
                return None

        if cur == "EUR":
            amt_eur = val
            amt_usd = _map_amount_shape_preserving(val, eur_to_usd)
            return amt_eur, amt_usd

        if cur == "USD":
            amt_usd = val
            amt_eur = _map_amount_shape_preserving(
                val, lambda x: _CCY.convert(x, "USD", "EUR", date=on_date)
            )
            return amt_eur, amt_usd

        amt_eur = _map_amount_shape_preserving(val, to_eur)
        amt_usd = _map_amount_shape_preserving(amt_eur, eur_to_usd) if amt_eur is not None else None
        return amt_eur, amt_usd

    converted = out.apply(_convert_row, axis=1)
    out[["amount_EUR", "amount_USD"]] = pd.DataFrame(converted.tolist(), index=out.index)
    return out

def run_investment_normalisation_pipeline(
    df_in: pd.DataFrame | None = None,
    input_path: str | None = None,
    output_path: str | None = None,
    *,
    write_outputs: bool = True,     # write the cleaned full df to output_path
    write_check: bool = True,       # write the small check file
) -> pd.DataFrame:
    
    """
    Normalise investment amounts & currencies.
    - If df_in is provided, use it (fast, in-memory).
    - Else read from input_path (Excel).
    Returns the *compact* df_out; the full enriched df is written only if write_outputs=True.
    """
    if df_in is not None:
        df = df_in.copy()
    else:
        if not input_path:
            raise ValueError("Provide either df_in or input_path.")
        df = pd.read_excel(input_path)

    # precleaning of investment values
    df["investment"] = df["investment"].fillna("").astype(str)
    df["investment_text"] = df["investment"].apply(_preclean_investment_text)

    # detect currency and clean text
    df["currency_iso"] = df["investment_text"].apply(detect_currency_iso)
    df["investment_text"] = df["investment_text"].apply(remove_currency_tokens)

    # adding dates from articleID
    id_to_date = get_article_id_to_date_map()
    df["date"] = df["article_id"].map(id_to_date)
    df["date"] = pd.to_datetime(df["date"], format="%Y-%m", errors="coerce")

    # parse amounts from the cleaned text
    parsed = df["investment_text"].apply(parse_amount_from_text)
    df[["raw_value", "amount_scalar", "investment_text"]] = pd.DataFrame(parsed.tolist(), index=df.index)
    df["amount_value"] = df.apply(
        lambda r: multiply_vals(r["raw_value"], r["amount_scalar"]),
        axis=1
    )

    df = add_year_and_fx_currencyconverter(
        df,
        date_col="date",
        currency_col="currency_iso",
        amount_col="amount_value"
    )

    # --- apply vehicle/battery 80/20 investment split ---
    df = distribute_vehicle_battery_split(
        df,
        id_col="investment_id",
        lv1_col="product_lv1",
        lv2_col="product_lv2",
        amount_cols=("amount_value", "amount_EUR", "amount_USD"),
    )

    def _round_shape_preserving(x, nd=0):
        # None/NaN passthrough
        if x is None or (isinstance(x, float) and pd.isna(x)):
            return None
        # List/tuple: round each element if numeric, keep None
        if isinstance(x, (list, tuple)):
            out = []
            for v in x:
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    out.append(None)
                else:
                    try:
                        out.append(round(float(v), nd))
                    except Exception:
                        out.append(None)
            return out
        # Scalar: try numeric then round
        try:
            return round(float(x), nd)
        except Exception:
            return None

    df["amount_EUR"] = df["amount_EUR"].apply(_round_shape_preserving)
    df["amount_USD"] = df["amount_USD"].apply(_round_shape_preserving)

    # select final columns
    df_out = df[[
        "investment",
        "investment_text",
        "amount_scalar",
        "currency_iso",
        "raw_value",
        "amount_value",   # <-- NEW in the output
        "date", "amount_EUR", "amount_USD", "year"
    ]]

    # write to Excel
    if write_check:
        check_path = "storage/output/check_investments.xlsx"
        df_out.to_excel(check_path, index=False)
    if write_outputs:
        if not output_path:
            raise ValueError("output_path is required when write_outputs=True.")
        df.to_excel(output_path, index=False)
        print(f"✅ Normalised investment file written to {output_path}")

    return df_out

# ======= Example call =======
df = run_investment_normalisation_pipeline(
    input_path="storage/output/investment-funds-factory.xlsx",
    output_path="storage/output/investment-funds-factory-clean.xlsx"
)
