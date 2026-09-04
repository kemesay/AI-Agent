"""Loads and queries the customs indicative-price reference table (supports Agent 7).

The reference workbook is public customs-commission indicative pricing, bundled with the
package at `data/customs_indicative_prices.xlsx` (see `core/config.py`'s default) so the
check works with no deployment setup; `CUSTOMS_PRICE_LIST_PATH` can override it with an
updated or replacement price list without rebuilding. Only the workbook's
first sheet ("selected Indicative price") is used; a second sheet in the source file is a
redundant detail-view duplicate of a subset of the first sheet's rows. The raw sheet is
messy — embedded section-divider rows (e.g. "FURNITURE", "ELECTRONICS", "METAL"), embedded
repeated-header rows where the table restarts mid-sheet, and inconsistent origin/unit-of-
measure spellings — all handled here so downstream code only ever sees clean, normalized
records.
"""

import logging
from dataclasses import dataclass
from functools import lru_cache

import openpyxl

from trade_service_agents.core.config import get_settings

LOGGER = logging.getLogger(__name__)

_SHEET_NAME = "selected Indicative price"
_HEADER_ROW = 2  # row 1 is a merged title; the real header row is row 2 (1-indexed)

# Aliases found in the raw data (e.g. "USA" vs "US", "PCS" vs "PC") normalized to one form.
_ORIGIN_ALIASES = {"USA": "US", "GB": "UK"}
_UNIT_ALIASES = {"UNIT": "UN", "PCS": "PC"}

# Minimum Jaccard word-overlap between an invoice's item description and a candidate
# reference row's description to treat it as a confident match. Tune with more real data.
_DESCRIPTION_MATCH_THRESHOLD = 0.2


@dataclass(frozen=True)
class ReferencePriceRecord:
    hs_code: int
    description: str
    unit: str
    origin: str
    price_usd: float


@dataclass(frozen=True)
class ReferencePriceMatch:
    record: ReferencePriceRecord
    similarity: float


def _normalize_origin(value: object) -> str:
    text = str(value).strip().upper()
    return _ORIGIN_ALIASES.get(text, text)


def _normalize_unit(value: object) -> str:
    text = str(value).strip().upper()
    return _UNIT_ALIASES.get(text, text)


def _normalize_hs_code(value: object) -> int | None:
    """Normalize a declared HS code to the reference table's 4-digit chapter granularity."""
    digits = "".join(ch for ch in str(value) if ch.isdigit())
    if len(digits) < 4:
        return None
    return int(digits[:4])


def load_customs_price_list(path: str) -> list[ReferencePriceRecord]:
    """Parse the customs indicative-price workbook into clean, normalized records.

    Skips section-divider rows (everything blank except a description like "METAL") and
    embedded repeated-header rows (literal strings like "HS " or "HS CODE" where the HS/price
    columns should be) that would otherwise break type coercion.
    """
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = workbook[_SHEET_NAME]
        records: list[ReferencePriceRecord] = []
        for row in sheet.iter_rows(min_row=_HEADER_ROW + 1, values_only=True):
            _, hs_raw, description, unit_raw, origin_raw, price_raw = row[:6]

            if hs_raw is None:
                continue  # section-divider row
            hs_code = _normalize_hs_code(hs_raw)
            if hs_code is None:
                continue  # unparsable / embedded repeated-header row

            try:
                price_usd = float(price_raw)
            except (TypeError, ValueError):
                continue  # embedded repeated-header row (price column holds header text)

            if not description:
                continue

            records.append(
                ReferencePriceRecord(
                    hs_code=hs_code,
                    description=str(description).strip(),
                    unit=_normalize_unit(unit_raw) if unit_raw else "",
                    origin=_normalize_origin(origin_raw) if origin_raw else "",
                    price_usd=price_usd,
                )
            )
        return records
    finally:
        workbook.close()


@lru_cache
def _cached_price_list(path: str) -> tuple[ReferencePriceRecord, ...]:
    return tuple(load_customs_price_list(path))


def get_reference_price_list() -> list[ReferencePriceRecord]:
    """Return the cached reference price list, or an empty list if unconfigured/unreadable.

    Never raises — this is optional, deployment-supplied data, and its absence should never
    crash a risk assessment.
    """
    path = get_settings().customs_price_list_path
    if not path:
        return []
    try:
        return list(_cached_price_list(path))
    except Exception:
        LOGGER.warning("Could not load customs price list from %s", path, exc_info=True)
        return []


def _word_overlap(a: str, b: str) -> float:
    """Jaccard similarity between two descriptions' word sets."""
    words_a = set(a.lower().split())
    words_b = set(b.lower().split())
    if not words_a or not words_b:
        return 0.0
    return len(words_a & words_b) / len(words_a | words_b)


def find_reference_price(
    records: list[ReferencePriceRecord],
    hs_code: str | None,
    description: str | None,
    origin: str | None = None,
) -> ReferencePriceMatch | None:
    """Find the best-matching reference record for an invoice line, or None if unconfident.

    Deliberately does not fall back to a description-only search across the whole table when
    `hs_code` is missing — with ~3500 heterogeneous rows spanning vehicles to furniture to
    steel, that would produce nonsense matches rather than correctly reporting no match.
    """
    normalized_hs = _normalize_hs_code(hs_code) if hs_code else None
    if normalized_hs is None or not description:
        return None

    candidates = [record for record in records if record.hs_code == normalized_hs]
    if not candidates:
        return None

    normalized_origin = _normalize_origin(origin) if origin else None
    if normalized_origin:
        origin_matches = [record for record in candidates if record.origin == normalized_origin]
        if origin_matches:
            candidates = origin_matches

    best: ReferencePriceMatch | None = None
    for record in candidates:
        similarity = _word_overlap(description, record.description)
        if best is None or similarity > best.similarity:
            best = ReferencePriceMatch(record=record, similarity=similarity)

    if best is None or best.similarity < _DESCRIPTION_MATCH_THRESHOLD:
        return None
    return best
