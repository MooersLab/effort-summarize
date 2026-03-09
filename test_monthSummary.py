"""Tests for monthSummary.py."""

import sqlite3
from datetime import datetime
from io import StringIO
from unittest.mock import patch

import pytest

import monthSummary as ms


# ── CATEGORIES and CATEGORY_NAMES ─────────────────────────────
# These mirror the weekly tests because the two scripts share
# the same category configuration.

class TestCategoriesConfiguration:
    """Validate the CATEGORIES list and derived CATEGORY_NAMES."""

    def test_categories_is_nonempty(self):
        assert len(ms.CATEGORIES) > 0

    def test_category_names_contains_lab_related(self):
        assert "Lab Related" in ms.CATEGORY_NAMES

    def test_category_names_contains_private(self):
        assert "Private" in ms.CATEGORY_NAMES

    def test_categories_match_weekly(self):
        """Both scripts must define the same ranges."""
        import weeklySummary as ws
        assert ms.CATEGORIES == ws.CATEGORIES
        assert ms.CATEGORY_NAMES == ws.CATEGORY_NAMES


# ── category_for() ────────────────────────────────────────────

class TestCategoryFor:
    """Test category_for() — same logic as weekly but exercised
    against the monthly module to ensure consistency."""

    @pytest.mark.parametrize("pid,expected", [
        ("1",    "Manuscripts"),
        ("999",  "Manuscripts"),
        ("1000", "Grants"),
        ("6300", "Lab Related"),
        ("6599", "Lab Related"),
        ("6620", "Lab Related"),
        ("6630", "Lab Related"),
        ("6900", "Lab Related"),
        ("6999", "Lab Related"),
        ("6000", "Private"),
        ("6299", "Private"),
        ("6600", "Private"),
        ("6619", "Private"),
        ("6631", "Private"),
        ("6899", "Private"),
        ("9999", "Workshops"),
    ])
    def test_category_lookups(self, pid, expected):
        assert ms.category_for(pid) == expected

    def test_empty_string(self):
        assert ms.category_for("") == "Uncategorized"

    def test_none(self):
        assert ms.category_for(None) == "Uncategorized"


# ── fetch_project_hours() ─────────────────────────────────────

class TestFetchProjectHours:
    """Test database queries for the monthly script."""

    def test_returns_rows_within_date_range(self, in_memory_db):
        rows = ms.fetch_project_hours(
            in_memory_db, "2026-03-01", "2026-03-31"
        )
        assert len(rows) > 0

    def test_full_month_captures_all_days(self, in_memory_db):
        rows = ms.fetch_project_hours(
            in_memory_db, "2026-03-01", "2026-03-31"
        )
        project_ids = {r[0] for r in rows}
        # Data exists on March 1, 2, and 3 — all should be included.
        assert "0100" in project_ids
        assert "8100" in project_ids
        assert "9100" in project_ids

    def test_excludes_empty_and_null(self, in_memory_db):
        rows = ms.fetch_project_hours(
            in_memory_db, "2026-03-01", "2026-03-31"
        )
        ids = [r[0] for r in rows]
        assert "" not in ids
        assert None not in ids


# ── print_org_table() ─────────────────────────────────────────

class TestPrintOrgTable:
    """Test monthly org-mode table output."""

    def _capture(self, rows, cat_totals, grand, start, end):
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            ms.print_org_table(rows, cat_totals, grand, start, end)
            return mock_out.getvalue()

    def test_caption_says_monthly(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-31"
        )
        assert "Monthly time summary" in out

    def test_booktabs_attribute(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-31"
        )
        assert ":booktabs t" in out


# ── print_latex_table() ───────────────────────────────────────

class TestPrintLatexTable:
    """Test monthly LaTeX table output."""

    def _capture(self, rows, cat_totals, grand, start, end):
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            ms.print_latex_table(rows, cat_totals, grand, start, end)
            return mock_out.getvalue()

    def test_caption_says_monthly(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-31"
        )
        assert "Monthly time summary" in out

    def test_booktabs_rules(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-31"
        )
        assert "\\toprule" in out
        assert "\\bottomrule" in out


# ── Month input parsing in main() ─────────────────────────────

class TestMonthInputParsing:
    """Test the interactive month/year prompts in main()."""

    def _run_main(self, month_str, year_str, db_conn):
        """Run main() with simulated input and return stdout."""
        inputs = iter([month_str, year_str])
        with patch("builtins.input", side_effect=inputs):
            with patch("monthSummary.sqlite3.connect", return_value=db_conn):
                with patch("sys.stdout", new_callable=StringIO) as mock_out:
                    ms.main()
                    return mock_out.getvalue()

    @pytest.fixture
    def empty_db(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("""
            CREATE TABLE zTimeSpent (
                DateDashed TEXT, ProjectID TEXT,
                ProjectDirectory TEXT, TimeHr REAL
            )
        """)
        yield conn
        conn.close()

    def test_full_month_name(self, empty_db):
        out = self._run_main("January", "2026", empty_db)
        assert "2026-01-01" in out
        assert "2026-01-31" in out

    def test_abbreviated_month_name(self, empty_db):
        out = self._run_main("Feb", "2026", empty_db)
        assert "2026-02-01" in out
        assert "2026-02-28" in out

    def test_partial_month_name(self, empty_db):
        out = self._run_main("mar", "2026", empty_db)
        assert "2026-03-01" in out
        assert "2026-03-31" in out

    def test_numeric_month(self, empty_db):
        out = self._run_main("4", "2026", empty_db)
        assert "2026-04-01" in out
        assert "2026-04-30" in out

    def test_default_month_and_year(self, empty_db):
        """Pressing Enter for both prompts uses the current month and year."""
        out = self._run_main("", "", empty_db)
        now = datetime.now()
        expected_start = "{:04d}-{:02d}-01".format(now.year, now.month)
        assert expected_start in out

    def test_february_leap_year(self, empty_db):
        out = self._run_main("February", "2024", empty_db)
        assert "2024-02-29" in out

    def test_february_non_leap_year(self, empty_db):
        out = self._run_main("February", "2025", empty_db)
        assert "2025-02-28" in out

    def test_invalid_month_name(self, empty_db):
        out = self._run_main("Smarch", "2026", empty_db)
        assert "Could not recognise month" in out

    def test_case_insensitive(self, empty_db):
        out = self._run_main("DECEMBER", "2026", empty_db)
        assert "2026-12-01" in out
        assert "2026-12-31" in out

    def test_december_has_31_days(self, empty_db):
        out = self._run_main("12", "2026", empty_db)
        assert "2026-12-31" in out


# ── Full integration ──────────────────────────────────────────

class TestMonthlyIntegration:
    """End-to-end tests with sample data."""

    def test_march_2026_full_run(self, in_memory_db):
        inputs = iter(["March", "2026"])
        with patch("builtins.input", side_effect=inputs):
            with patch("monthSummary.sqlite3.connect",
                       return_value=in_memory_db):
                with patch("sys.stdout", new_callable=StringIO) as mock_out:
                    ms.main()
                    output = mock_out.getvalue()

        # Org table assertions
        assert "#+CAPTION:" in output
        assert "Monthly time summary" in output

        # LaTeX table assertions
        assert "\\begin{table}" in output
        assert "\\end{table}" in output

        # Specific project from fixture
        assert "rna_crystal_ms" in output
        assert "Grand Total" in output

    def test_lab_related_subtotal_present(self, in_memory_db):
        inputs = iter(["3", "2026"])
        with patch("builtins.input", side_effect=inputs):
            with patch("monthSummary.sqlite3.connect",
                       return_value=in_memory_db):
                with patch("sys.stdout", new_callable=StringIO) as mock_out:
                    ms.main()
                    output = mock_out.getvalue()

        assert "Lab Related" in output

    def test_uncategorized_appears_for_orphan_project(self, in_memory_db):
        """ProjectID 4000 falls outside all ranges."""
        inputs = iter(["3", "2026"])
        with patch("builtins.input", side_effect=inputs):
            with patch("monthSummary.sqlite3.connect",
                       return_value=in_memory_db):
                with patch("sys.stdout", new_callable=StringIO) as mock_out:
                    ms.main()
                    output = mock_out.getvalue()

        assert "Uncategorized" in output
