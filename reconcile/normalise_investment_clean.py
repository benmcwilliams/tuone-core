import os, re, sys, math, unicodedata
import pandas as pd
from currency_converter import CurrencyConverter
import pycountry
from numerizer import numerize
from word2number import w2n
from currency_symbols import CurrencySymbols
from forex_python.converter import CurrencyRates  # kept for parity
from src.id_date_dict import get_article_id_to_date_map
from src.split_investments import _as_iter, _is_missing, multiply_vals, distribute_vehicle_battery_split

# --- Currency metadata ---
def _strip_accents(s): return "".join(ch for ch in unicodedata.normalize("NFKD", s) if not unicodedata.combining(ch))
def _normalize_spaces(s): return re.sub(r"\s+", " ", s).strip()

currency_list = [(c.alpha_3, CurrencySymbols.get_symbol(c.alpha_3) or "", c.name) for c in pycountry.currencies]
ALL_ISOS = {iso for iso, _, _ in currency_list}
NAME_ALIASES = {...}  # same content as before
NAME_TO_ISO = {**NAME_ALIASES, **{n.lower(): iso for iso, _, n in currency_list if n}}
NAME_TO_ISO.update({f"{n}s": iso for n, iso in NAME_TO_ISO.items() if not n.endswith("s")})
SCANDI_ADJ_TO_ISO = {"swedish": "SEK", "norwegian": "NOK", "danish": "DKK", "icelandic": "ISK"}
SYMBOL_TO_ISO = {...}  # same mapping
MULTI_SYMBOL_TO_ISO = {"us$": "USD", "u.s.$": "USD", "u$s": "USD", "c$": "CAD", "a$": "AUD", "nz$": "NZD", "ƒ,ª": "EUR"}
COUNTRY_TOKEN_RE = re.compile(r"\b(u\.?s\.?a?\.?|united states|u\.?k\.?|united kingdom|great britain)\b", re.I)
KRON_WORDS_RE = re.compile(r"\b(krona|kronor|krone|kroner|krA3nur|krA3na)\b", re.I)
NAME_TOKEN_RE = re.compile(r"\b(?:%s)\b" % "|".join(re.escape(n) for n in sorted(NAME_TO_ISO, key=len, reverse=True)), re.I)
CURRENCY_TOKEN_RE = re.compile(
    rf"(?P<iso>\b[A-Za-z]{{3}}\b)|(?P<name>\b(?:{'|'.join(map(re.escape, sorted(NAME_TO_ISO, key=len, reverse=True)))})\b)|(?P<sym>(?:{'|'.join(map(re.escape, SYMBOL_TO_ISO))}))",
    re.I,
)

def detect_currency_iso(text):
    if not isinstance(text, str) or not text.strip(): return None
    t, t_fold = text, _strip_accents(text).lower()
    if any(msym in t_fold for msym in MULTI_SYMBOL_TO_ISO): return next(iso for msym, iso in MULTI_SYMBOL_TO_ISO.items() if msym in t_fold)
    for m in re.finditer(r'(?<![A-Za-z])([A-Za-z]{3})(?=\d)', t):  # ISO stuck to number
        if (iso := m.group(1).upper()) in ALL_ISOS: return iso
    for m in re.finditer(r"\b([A-Za-z]{3})\b", t):
        if (iso := m.group(1).upper()) in ALL_ISOS: return iso
    if (KRON_WORDS_RE.search(t_fold) or "kron" in t_fold) and (adj_iso := next((iso for adj, iso in SCANDI_ADJ_TO_ISO.items() if re.search(rf"\b{adj}\b", t_fold)), None)): return adj_iso
    if (m := NAME_TOKEN_RE.search(t_fold)): return NAME_TO_ISO.get(m.group(0).lower())
    if COUNTRY_TOKEN_RE.search(t_fold) and re.search(r"\$|\d", t_fold):
        token = COUNTRY_TOKEN_RE.search(t_fold).group(0).replace(".", "").replace(" ", "")
        return "USD" if token.startswith("u") else "GBP"
    for sym, iso in SYMBOL_TO_ISO.items():
        if sym in t: return iso
    return "MXN" if "$" in t and "peso" in t_fold else ("USD" if "$" in t else None)

def remove_currency_tokens(text):
    if not isinstance(text, str) or not text.strip(): return text
    cleaned = text
    for msym in MULTI_SYMBOL_TO_ISO: cleaned = re.sub(re.escape(msym), " ", cleaned, flags=re.I)
    def drop(m):
        iso, name, sym = m.group("iso"), m.group("name"), m.group("sym")
        if sym or name: return " "
        return " " if iso and iso.upper() in ALL_ISOS else m.group(0)
    cleaned = CURRENCY_TOKEN_RE.sub(drop, cleaned)
    cleaned = re.sub(r'(?<![A-Za-z])([A-Za-z]{3})(?=\d)', lambda m: " " if m.group(1).upper() in ALL_ISOS else m.group(0), cleaned)
    return _normalize_spaces(KRON_WORDS_RE.sub(" ", cleaned).replace("$", " "))

# --- Amount parsing helpers ---
SCALE_MAP = {...}  # same content
DIGIT_WORD_MAP = {...}
SCALE_TOKEN = r"(thousand|million|billion|trillion|k|m|mn|mln|b|bn|bln)"
PREFIX_RE = re.compile(r"^(?P<prefix>up to|less than|under|more than|over|well over|about|around|approximately|approx|nearly|almost|close to)\b\s*", re.I)
REGEX_PATTERNS = {...}  # keep names, values identical

def _parse_digit_count(tok):
    t = tok.lower()
    if t.isdigit(): return int(t)
    if t in DIGIT_WORD_MAP: return DIGIT_WORD_MAP[t]
    try: return w2n.word_to_num(t)
    except Exception: return None

def _to_float(s):
    s = s.strip().replace('\u00a0', ' ')
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.') if s.rfind(',') > s.rfind('.') else s.replace(',', '')
    elif ',' in s:
        s = s.replace(',', '') if re.match(r'^\d{1,3}(,\d{3})+$', s) else s.replace(',', '.')
    return float(s.replace(' ', ''))

def _wrap_inequality(prefix, raw, scalar, rest):
    if not prefix or isinstance(raw, list): return raw, scalar, rest
    p = prefix.lower()
    if p in ("about", "around", "approximately", "approx", "nearly", "almost", "close to"): return raw, scalar, rest
    if p in ("up to", "less than", "under"): return [None, raw], scalar, rest
    if p in ("more than", "over", "well over"): return [raw, None], scalar, rest
    return raw, scalar, rest

def parse_amount_from_text(text_clean):
    if not isinstance(text_clean, str): return (None, None, None)
    text = text_clean.strip()
    m_pref = PREFIX_RE.match(text); prefix = m_pref.group("prefix") if m_pref else None
    text = text[m_pref.end():].lstrip() if m_pref else text

    def match(pattern, fn):
        m = re.match(pattern, text, re.I)
        return fn(m) if m else None

    # ordered pattern checks (same logic condensed)
    if out := match(REGEX_PATTERNS["word_range_scale"], lambda m: ([w2n.word_to_num(m[1]), w2n.word_to_num(m[2])], SCALE_MAP.get(m[3].lower()), m[4])): return out
    if out := match(REGEX_PATTERNS["range_numeric"], lambda m: ([ _to_float(m[1]), _to_float(m[2]) ], SCALE_MAP.get(m_scale.group("scale").lower()) if (m_scale := re.match(rf"^(?P<scale>{SCALE_TOKEN})\b\s*(?P<rest>.*)", m[3], re.I)) else None, (m_scale.group("rest") if m_scale else m[3]).strip())): return out
    if out := match(REGEX_PATTERNS["range_with_scale"], lambda m: ([ _to_float(m[1]), _to_float(m[3]) ], SCALE_MAP[m[2].lower()] if SCALE_MAP.get(m[2].lower()) == SCALE_MAP.get(m[4].lower()) else None, m[5])): return out
    if out := match(REGEX_PATTERNS["digit_scale"], lambda m: ([(10 ** (_parse_digit_count(m[1]) - 1)) * SCALE_MAP[m[2].lower()], (10 ** _parse_digit_count(m[1]) - 1) * SCALE_MAP[m[2].lower()]], None, m[3]) if (SCALE_MAP.get(m[2].lower()) and _parse_digit_count(m[1]) and _parse_digit_count(m[1]) >= 2) else None): return out
    if out := match(REGEX_PATTERNS["num_with_scale_stuck"], lambda m: _wrap_inequality(prefix, _to_float(m[1]), SCALE_MAP.get(m[2].lower()), m[3])): return out
    if out := match(REGEX_PATTERNS["mixed_fraction_scaled"], lambda m: _wrap_inequality(prefix, (float(m[1]) if m[1].isdigit() else w2n.word_to_num(m[1])) + 0.5, SCALE_MAP.get(m[2].lower()), m[3])): return out
    if out := match(REGEX_PATTERNS["unified_amount"], lambda m: _wrap_inequality(prefix, _to_float(m[1]) if re.fullmatch(r"[0-9.,]+", m[1].strip()) else w2n.word_to_num(m[1].strip()), SCALE_MAP.get(m[2].lower()) if m[2] else None, m[3]) if not re.search(r"\bdigit\b", m[1], re.I) else None): return out
    if out := match(REGEX_PATTERNS["plain_numeric_unit"], lambda m: _wrap_inequality(prefix, _to_float(m[1]), None, m[2].strip())): return out
    try:
        numerized = numerize(text.lower())
        if m := re.match(REGEX_PATTERNS["fallback"], numerized, re.I):
            return _wrap_inequality(prefix, _to_float(m[1]), SCALE_MAP.get((m[2] or "").lower()) if m[2] else None, m[3].strip())
    except Exception:
        pass
    return None, None, text

# --- FX + pipeline ---
_CCY = CurrencyConverter(fallback_on_missing_rate=True, fallback_on_wrong_date=True)

def _map_amount_shape_preserving(val, fn):
    if val is None or (isinstance(val, float) and pd.isna(val)): return None
    if isinstance(val, (list, tuple)): return [None if (v is None or (isinstance(v, float) and pd.isna(v))) else fn(v) if pd.notna(fn(v)) else None for v in val]
    return fn(val)

def add_year_and_fx(df, date_col="date", currency_col="currency_iso", amount_col="amount_value"):
    if df.empty: return df.assign(year=pd.Series(dtype="Int64"), amount_EUR=pd.Series(dtype="object"), amount_USD=pd.Series(dtype="object"))
    out = df.copy()
    out[date_col] = pd.to_datetime(out[date_col], errors="coerce")
    out["year"] = out[date_col].dt.year.astype("Int64")

    def convert(row):
        cur, val, dt = (row.get(currency_col) or "").upper(), row.get(amount_col), row.get(date_col)
        on_date = dt.date() if pd.notna(dt) else None
        to_eur = (lambda x: x) if cur == "EUR" else (lambda x: _CCY.convert(x, cur, "EUR", date=on_date))
        eur_to_usd = lambda x: _CCY.convert(x, "EUR", "USD", date=on_date)
        if cur == "USD":
            amt_usd = val
            amt_eur = _map_amount_shape_preserving(val, lambda x: _CCY.convert(x, "USD", "EUR", date=on_date))
        else:
            amt_eur = _map_amount_shape_preserving(val, to_eur)
            amt_usd = _map_amount_shape_preserving(amt_eur, eur_to_usd) if amt_eur is not None else None
        return amt_eur, _map_amount_shape_preserving(amt_eur if cur == "EUR" else amt_usd, eur_to_usd) if cur == "EUR" else amt_usd

    out[["amount_EUR", "amount_USD"]] = pd.DataFrame(out.apply(convert, axis=1).tolist(), index=out.index)
    return out

def run_investment_normalisation_pipeline(df_in=None, input_path=None, output_path=None, *, write_outputs=True, write_check=True):
    df = df_in.copy() if df_in is not None else pd.read_excel(input_path) if input_path else ValueError("Provide df_in or input_path.")
    df["investment_text"] = df["investment"].fillna("").astype(str).pipe(_drop_parentheses).pipe(_soft_remove_dashes).apply(_normalize_spaces)
    df["currency_iso"] = df["investment_text"].apply(detect_currency_iso)
    df["investment_text"] = df["investment_text"].apply(remove_currency_tokens)
    df["date"] = pd.to_datetime(df["article_id"].map(get_article_id_to_date_map()), format="%Y-%m", errors="coerce")
    parsed = df["investment_text"].apply(parse_amount_from_text)
    df[["raw_value", "amount_scalar", "investment_text"]] = pd.DataFrame(parsed.tolist(), index=df.index)
    df["amount_value"] = df.apply(lambda r: multiply_vals(r["raw_value"], r["amount_scalar"]), axis=1)
    df = add_year_and_fx(df, "date", "currency_iso", "amount_value")
    df = distribute_vehicle_battery_split(df, "investment_id", "product_lv1", "product_lv2", ("amount_value", "amount_EUR", "amount_USD"))
    rounder = lambda x: None if x is None or (isinstance(x, float) and pd.isna(x)) else [round(float(v), 0) if v is not None else None for v in x] if isinstance(x, (list, tuple)) else round(float(x), 0)
    df["amount_EUR"], df["amount_USD"] = df["amount_EUR"].apply(rounder), df["amount_USD"].apply(rounder)
    df_out = df[["investment", "investment_text", "amount_scalar", "currency_iso", "raw_value", "amount_value", "date", "amount_EUR", "amount_USD", "year"]]
    if write_check: df_out.to_excel("storage/output/check_investments.xlsx", index=False)
    if write_outputs and output_path: df.to_excel(output_path, index=False)
    return df_out