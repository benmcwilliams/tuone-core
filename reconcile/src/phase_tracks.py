import re
import pandas as pd

def parse_phase_num_and_track(val):
    """
    Parse phase tags like '1A', '2B', '3', etc.

    Returns (phase_num_int, track_letter_or_None).

    Examples:
      '1A' -> (1, 'A')
      '2b' -> (2, 'B')
      '3'  -> (3, None)
      None / NaN / weird -> (None, None)
    """
    if pd.isna(val):
        return None, None

    s = str(val).strip().upper()

    # pattern: digits + optional single trailing letter, e.g. '1A', '12B', '3'
    m = re.fullmatch(r"(\d+)([A-Z])?", s)
    if not m:
        return None, None

    num_str, letter = m.group(1), m.group(2)
    try:
        num = int(num_str)
    except ValueError:
        return None, None

    return num, (letter if letter else None)