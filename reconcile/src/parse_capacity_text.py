import re
from numerizer import numerize
import logging
from word2number import w2n

# ========= Scale Mapping =========
SCALE_MAP = {
    # Thousand
    "thousand": 1e3, "thousands": 1e3,
    "k": 1e3, "K": 1e3,
    "kilo": 1e3, "kilos": 1e3,
    
    # Million
    "million": 1e6, "millions": 1e6,
    "m": 1e6, "M": 1e6,
    "mn": 1e6, "MN": 1e6,
    "mln": 1e6, "MLN": 1e6,
    
    # Billion
    "billion": 1e9, "billions": 1e9,
    "b": 1e9, "B": 1e9,
    "bn": 1e9, "BN": 1e9,
    "bln": 1e9, "BLN": 1e9,
    
    # Trillion
    "trillion": 1e12, "trillions": 1e12,
    #"t": 1e12, "T": 1e12,
    #"tn": 1e12, "TN": 1e12,
    "trn": 1e12, "TRN": 1e12
}

# ========= Regex Patterns =========
REGEX_PATTERNS = {
    "range": r"^([0-9,.]+)\s*(?:to|-|–|—)\s*([0-9,.]+)\s+(.*)",
    
    "approx_scaled": r"^(almost|nearly|around|about|approximately|approx\.?|over|under|more than|less than)\s+([0-9,.]+)\s+(thousand|million|billion|trillion)\b\s*(.*)",
    
    "approx": r"^(almost|nearly|around|about|approximately|approx\.?|over|under|more than|less than|up to)\s+([0-9,.]+)\s+(.*)",
    
    "fractional_half": r"^(half|a half|one half|one and a half| half a)\s+(thousand|million|billion|trillion)\b\s*(.*)",
    
    "compound_word_scale": r"^([a-z\s-]+)\s+(thousand|million|billion|trillion)\b\s*(.*)",
    
    "num_with_scale": r"^([0-9,.]+)\s+(thousand|million|billion|trillion)\b\s*(.*)",
    
    "word_with_scale": r"^([a-z\s-]+)\s+(thousand|million|billion|trillion)\b\s*(.*)",
    
    "num_with_scale_stuck": r"^([0-9.,]+)\s*([a-zA-Z]+)\b\s*(.*)",
    
    "plain_numeric": r"^([0-9,.]+)\s*([a-zA-Z/]+.*)",

    "mixed_fraction_scaled": r"^([a-z0-9\s-]+?)\s+and a half\s+(thousand|million|billion|trillion)\b\s*(.*)",
    
    "fallback" : r"^([0-9,.]+)\s*(thousand|million|billion|trillion)?\b\s*(.*)" 

}

## ========= Parse =========
# ========= Capacity Info Extraction =========
def parse_capacity_text(text):
    if not isinstance(text, str):
        return None, None, None
    text = text.strip()

    # Case: Range (e.g., 1,000–2,000 tonnes)
    match = re.match(REGEX_PATTERNS["range"], text, re.IGNORECASE)
    if match:
        logging.debug(f"Case range: {match}")
        try:
            val1 = float(match.group(1).replace(",", ""))
            val2 = float(match.group(2).replace(",", ""))
            remaining = match.group(3).strip()
            return [val1, val2], None, remaining
        except:
            pass

    # Case: Approximate with scale (e.g., about 1 million)
    match = re.match(REGEX_PATTERNS["approx_scaled"], text, re.IGNORECASE)
    if match:
        logging.debug(f"Case approximate scale: {match}")
        try:
            value = float(match.group(2).replace(",", ""))
            scale = SCALE_MAP.get(match.group(3).lower())
            remaining = match.group(4).strip()
            return value, scale, remaining
        except:
            pass

    # Case: Approximate without scale (e.g., about 2000)
    match = re.match(REGEX_PATTERNS["approx"], text, re.IGNORECASE)
    if match:
        logging.debug(f"Case approximate without scale: {match}")
        try:
            value = float(match.group(2).replace(",", ""))
            remaining = match.group(3).strip()
            return value, None, remaining
        except:
            pass

    # Case: Mixed fraction (e.g., "three and a half million")
    match = re.match(REGEX_PATTERNS["mixed_fraction_scaled"], text, re.IGNORECASE)
    if match:
        logging.debug(f"Mixed fraction: {match}")
        try:
            whole = match.group(1).strip()
            scale_str = match.group(3).lower()
            remaining = match.group(4).strip()
            scale = SCALE_MAP.get(scale_str)
            if scale:
                if whole.isdigit():
                    whole_val = float(whole)
                else:
                    whole_val = w2n.word_to_num(whole)
                return whole_val + 0.5, scale, remaining
        except:
            pass

    # Case: Word + scale (e.g., one million)
    match = re.match(REGEX_PATTERNS["word_with_scale"], text, re.IGNORECASE)
    if match:
        logging.debug(f"Case word with scale: {match}")
        try:
            value = w2n.word_to_num(match.group(1).strip())
            scale = SCALE_MAP.get(match.group(2).lower())
            remaining = match.group(3).strip()
            return value, scale, remaining
        except:
            pass

    # Case: Numeric + scale (e.g., 2 million)
    match = re.match(REGEX_PATTERNS["num_with_scale"], text, re.IGNORECASE)
    if match:
        logging.debug(f"Case numeric with scale: {match}")
        try:
            value = float(match.group(1).replace(",", ""))
            scale = SCALE_MAP.get(match.group(2).lower())
            remaining = match.group(3).strip()
            return value, scale, remaining
        except:
            pass

    # Case: Numeric + suffix (e.g., 5k, 12.3B)
    match = re.match(REGEX_PATTERNS["num_with_scale_stuck"], text, re.IGNORECASE)
    if match:
        logging.debug(f"Case num with scale stuck: {match}")
        try:
            num_str, suffix, remaining = match.groups()
            value = float(num_str.replace(",", ""))
            scl = SCALE_MAP.get(suffix.lower())
            if scl:
                return value, scl, remaining.strip()
        except Exception:
            pass

    # Case: Numeric stuck to unit (e.g., 20GWh, 1000MW/year)
    match = re.match(REGEX_PATTERNS["plain_numeric"], text, re.IGNORECASE)
    if match:
        logging.debug(f"Numeric stuck to unit: {match}")
        try:
            value = float(match.group(1).replace(",", ""))
            remaining = match.group(2).strip()
            return value, None, remaining
        except:
            pass

    # Fallback: Clean and parse with numerizer
    try:
        modifiers = ["up to", "about", "around", "approximately", "approx", "nearly", "almost", "more than", "less than", "over", "under"]
        text_lower = text.lower()
        for mod in modifiers:
            if text_lower.startswith(mod):
                text_lower = text_lower[len(mod):].strip()
                break

        numerized = numerize(text_lower)
        match = re.match(REGEX_PATTERNS["fallback"], numerized, re.IGNORECASE)
        if match:
            value = float(match.group(1).replace(",", ""))
            scale_str = match.group(2)
            remaining = match.group(3).strip()
            scale = SCALE_MAP.get(scale_str.lower()) if scale_str else None
            return value, scale, remaining
    except:
        pass

    return None, None, text
