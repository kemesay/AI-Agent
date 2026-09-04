import openpyxl
import pytest

from trade_service_agents.core.config import _DEFAULT_CUSTOMS_PRICE_LIST_PATH
from trade_service_agents.reference_data.customs_prices import (
    ReferencePriceRecord,
    find_reference_price,
    load_customs_price_list,
)


def test_bundled_default_price_list_loads_successfully():
    """Regression guard: catches packaging mistakes (e.g. forgetting package-data) that would
    silently degrade this to a no-op in a real deployment."""
    records = load_customs_price_list(_DEFAULT_CUSTOMS_PRICE_LIST_PATH)
    assert len(records) > 1000
    assert all(isinstance(r.hs_code, int) and r.description for r in records)


@pytest.fixture
def synthetic_workbook_path(tmp_path):
    """A small workbook reproducing the real file's messiness: a merged title row, embedded
    section-divider rows, an embedded repeated-header row, and origin/unit alias variants."""
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "selected Indicative price"

    sheet.append(["TABLE 1: INDICATIVE PRICE FOR SELECTED IMPORT ITEMS"])
    sheet.append(["S.NO", "HS ", "DESCRIPTION", "UNIT OF MEASUREMENT", "ORIGIN", "UNIT PRICE (in USD)"])
    sheet.append([1, 8703, "TOYOTA HILUX PICKUP D/CAB", "UN", "CN", 37708])
    sheet.append([2, 8703, "BYD SONG PLUS PREMIUM EDITION", "UNIT", "USA", 22040])
    sheet.append([3, None, "FURNITURE", None, None, None])  # section-divider row
    sheet.append(["HS ", "DESCRIPTION", "UNIT", "ORIGIN", "FOB USD"])  # embedded repeated header
    sheet.append([4, 9403, "S/S TABLE LEG BASE", "PCS", "GB", 41.33])
    sheet.append([5, 7301, "ANGLE IRON (EQUAL ANGLE)", "MT", "TR", 600])
    sheet.append([6, 7301, "ANGLE IRON (EQUAL ANGLE)", "MT", "CN", 505])

    path = tmp_path / "synthetic_prices.xlsx"
    workbook.save(path)
    return str(path)


def test_load_customs_price_list_skips_dividers_and_repeated_headers(synthetic_workbook_path):
    records = load_customs_price_list(synthetic_workbook_path)

    # 5 real data rows; the divider row and the embedded repeated-header row are skipped.
    assert len(records) == 5
    assert all(isinstance(r, ReferencePriceRecord) for r in records)
    assert all(isinstance(r.hs_code, int) for r in records)
    assert all(isinstance(r.price_usd, float) for r in records)


def test_load_customs_price_list_normalizes_origin_and_unit_aliases(synthetic_workbook_path):
    records = load_customs_price_list(synthetic_workbook_path)
    byd = next(r for r in records if "BYD" in r.description)
    table_leg = next(r for r in records if "TABLE LEG" in r.description)

    assert byd.origin == "US"  # normalized from "USA"
    assert byd.unit == "UN"  # normalized from "UNIT"
    assert table_leg.origin == "UK"  # normalized from "GB"
    assert table_leg.unit == "PC"  # normalized from "PCS"


def test_load_customs_price_list_parses_hs_chapter_code(synthetic_workbook_path):
    records = load_customs_price_list(synthetic_workbook_path)
    assert {r.hs_code for r in records} == {8703, 9403, 7301}


def test_find_reference_price_filters_by_hs_code(synthetic_workbook_path):
    records = load_customs_price_list(synthetic_workbook_path)
    match = find_reference_price(records, hs_code="9403", description="S/S TABLE LEG BASE")
    assert match is not None
    assert match.record.hs_code == 9403


def test_find_reference_price_prefers_origin_match_on_tie(synthetic_workbook_path):
    records = load_customs_price_list(synthetic_workbook_path)
    match = find_reference_price(
        records, hs_code="7301", description="ANGLE IRON (EQUAL ANGLE)", origin="CN"
    )
    assert match is not None
    assert match.record.origin == "CN"
    assert match.record.price_usd == 505


def test_find_reference_price_returns_none_when_hs_code_missing(synthetic_workbook_path):
    records = load_customs_price_list(synthetic_workbook_path)
    assert find_reference_price(records, hs_code=None, description="ANGLE IRON") is None


def test_find_reference_price_returns_none_when_description_does_not_match(synthetic_workbook_path):
    records = load_customs_price_list(synthetic_workbook_path)
    # Same HS chapter (8703) exists, but nothing about "unrelated widget" overlaps with
    # either "TOYOTA HILUX PICKUP D/CAB" or "BYD SONG PLUS PREMIUM EDITION".
    match = find_reference_price(records, hs_code="8703", description="unrelated widget")
    assert match is None


def test_find_reference_price_returns_none_for_unmatched_hs_code(synthetic_workbook_path):
    records = load_customs_price_list(synthetic_workbook_path)
    assert find_reference_price(records, hs_code="9999", description="anything") is None
