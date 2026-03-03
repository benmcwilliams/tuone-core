import logging
from typing import List, Optional, Any

import pandas as pd

# Optional global tracker set by main.py when debug_article_id is in use; cleared when not.
_debug_tracker: Optional["DebugArticleTracker"] = None


def get_debug_tracker() -> Optional["DebugArticleTracker"]:
    return _debug_tracker


def set_debug_tracker(tracker: Optional["DebugArticleTracker"]) -> None:
    global _debug_tracker
    _debug_tracker = tracker


class DebugArticleTracker:
    """
    Writes diagnostic messages for a single article to a dedicated log file only
    (no main console output). Used for row-count checkpoints and drop-reason summaries.
    """

    def __init__(self, article_id: str, logger: logging.Logger):
        self.article_id = article_id
        self._log = logger
        self._diagnosis_bullets: List[str] = []

    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.info(msg, *args, **kwargs)

    def warn(self, msg: str, *args: Any, **kwargs: Any) -> None:
        self._log.warning(msg, *args, **kwargs)

    def section(self, title: str) -> None:
        self._log.info("")
        self._log.info("=== %s ===", title)
        self._log.info("")

    def checkpoint(self, stage_name: str, row_count: int, detail: Optional[str] = None) -> None:
        line = f"[{stage_name}] rows for article: %d" % row_count
        if detail:
            line += " — %s" % detail
        self._log.info(line)

    def drop_reason(self, stage_name: str, reason: str, detail: Optional[str] = None) -> None:
        line = f"[{stage_name}] %s" % reason
        if detail:
            line += " — %s" % detail
        self._log.warning(line)
        self._diagnosis_bullets.append(f"{stage_name}: {reason}")

    def add_diagnosis_bullet(self, text: str) -> None:
        self._diagnosis_bullets.append(text)
        self._log.info("Diagnosis: %s", text)

    def get_diagnosis_bullets(self) -> List[str]:
        return list(self._diagnosis_bullets)

    def clear_diagnosis_bullets(self) -> None:
        self._diagnosis_bullets.clear()


def debug_print_df(
    df: pd.DataFrame,
    label: str,
    cols: List[str],
    debug_article_id: Optional[str],
    tracker: Optional[DebugArticleTracker] = None,
) -> None:
    """
    Log a compact view of rows for a single article_id in debug mode.
    When tracker is provided (and matches debug_article_id), writes only to the
    per-article log file. Otherwise no-op if debug_article_id is None.
    """
    if not debug_article_id:
        return

    t = tracker if tracker is not None else get_debug_tracker()
    use_tracker = (t is not None and t.article_id == debug_article_id)

    if "article_id" not in df.columns:
        msg = f"[DEBUG {label}] article_id={debug_article_id}: 'article_id' column missing"
        if use_tracker:
            t.info(msg)
        return

    sub = df.loc[df["article_id"] == debug_article_id].copy()
    if sub.empty:
        msg = f"[DEBUG {label}] article_id={debug_article_id}: no rows in this frame"
        if use_tracker:
            t.info(msg)
        return

    existing_cols = [c for c in cols if c in sub.columns]
    if existing_cols:
        sub = sub[existing_cols]

    msg = f"[DEBUG {label}] article_id={debug_article_id} ({len(sub)} rows):\n{sub.to_string(index=False)}"
    if use_tracker:
        t.info("%s", msg)
