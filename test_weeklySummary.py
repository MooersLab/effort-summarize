"""Tests for weeklySummary.py."""

import sqlite3
from datetime import datetime, timedelta
from io import StringIO
from unittest.mock import patch

import pytest

import weeklySummary as ws


# ── CATEGORIES and CATEGORY_NAMES ─────────────────────────────

class TestCategoriesConfiguration:
    """Validate the CATEGORIES list and derived CATEGORY_NAMES."""

    def test_categories_is_nonempty(self):
        assert len(ws.CATEGORIES) > 0

    def test_category_tuples_have_three_elements(self):
        for entry in ws.CATEGORIES:
            assert len(entry) == 3, "Expected (name, lo, hi): {}".format(entry)

    def test_ranges_are_non_negative_and_ordered(self):
        for name, lo, hi in ws.CATEGORIES:
            assert lo >= 0, "{}: lo < 0".format(name)
            assert hi >= lo, "{}: hi < lo".format(name)

    def test_no_overlapping_ranges(self):
        """Adjacent ranges must not overlap."""
        sorted_cats = sorted(ws.CATEGORIES, key=lambda c: c[1])
        for i in range(len(sorted_cats) - 1):
            _, _, hi = sorted_cats[i]
            _, lo_next, _ = sorted_cats[i + 1]
            assert lo_next > hi, (
                "Overlap between {} (hi={}) and {} (lo={})".format(
                    sorted_cats[i], hi, sorted_cats[i + 1], lo_next
                )
            )

    def test_category_names_are_unique_and_ordered(self):
        seen = []
        for name in ws.CATEGORY_NAMES:
            assert name not in seen, "Duplicate in CATEGORY_NAMES: {}".format(name)
            seen.append(name)

    def test_category_names_contains_lab_related(self):
        assert "Lab Related" in ws.CATEGORY_NAMES

    def test_category_names_contains_private(self):
        assert "Private" in ws.CATEGORY_NAMES

    def test_lab_related_appears_after_private(self):
        idx_priv = ws.CATEGORY_NAMES.index("Private")
        idx_lab = ws.CATEGORY_NAMES.index("Lab Related")
        assert idx_lab == idx_priv + 1


# ── category_for() ────────────────────────────────────────────

class TestCategoryFor:
    """Test the category_for() function across all ranges and edge cases."""

    @pytest.mark.parametrize("pid,expected", [
        ("1",    "Manuscripts"),
        ("500",  "Manuscripts"),
        ("999",  "Manuscripts"),
        ("1000", "Grants"),
        ("1999", "Grants"),
        ("2000", "Books"),
        ("2999", "Books"),
        ("3000", "Talks"),
        ("3999", "Talks"),
        ("4001", "Posters"),
        ("4150", "Posters"),
        ("4151", "Software Repositories"),
        ("4999", "Software Repositories"),
        ("5000", "Manuscript Reviews"),
        ("5999", "Manuscript Reviews"),
    ])
    def test_standard_categories(self, pid, expected):
        assert ws.category_for(pid) == expected

    @pytest.mark.parametrize("pid,expected", [
        ("6000", "Private"),
        ("6299", "Private"),
        ("6300", "Lab Related"),
        ("6450", "Lab Related"),
        ("6599", "Lab Related"),
        ("6600", "Private"),
        ("6619", "Private"),
        ("6620", "Lab Related"),
        ("6625", "Lab Related"),
        ("6630", "Lab Related"),
        ("6631", "Private"),
        ("6899", "Private"),
        ("6900", "Lab Related"),
        ("6950", "Lab Related"),
        ("6999", "Lab Related"),
    ])
    def test_private_and_lab_related_boundaries(self, pid, expected):
        assert ws.category_for(pid) == expected

    @pytest.mark.parametrize("pid,expected", [
        ("7000", "Service"),
        ("7999", "Service"),
        ("8000", "Teaching"),
        ("8999", "Teaching"),
        ("9000", "Workshops"),
        ("9999", "Workshops"),
    ])
    def test_upper_categories(self, pid, expected):
        assert ws.category_for(pid) == expected

    def test_uncategorized_for_gap(self):
        assert ws.category_for("4000") == "Uncategorized"

    def test_uncategorized_for_zero(self):
        assert ws.category_for("0") == "Uncategorized"

    def test_uncategorized_above_max(self):
        assert ws.category_for("10000") == "Uncategorized"

    def test_empty_string_returns_uncategorized(self):
        assert ws.category_for("") == "Uncategorized"

    def test_none_returns_uncategorized(self):
        assert ws.category_for(None) == "Uncategorized"

    def test_non_numeric_returns_uncategorized(self):
        assert ws.category_for("abc") == "Uncategorized"

    def test_integer_input_works(self):
        assert ws.category_for(500) == "Manuscripts"


# ── fetch_project_hours() ─────────────────────────────────────

class TestFetchProjectHours:
    """Test database queries using an in-memory SQLite fixture."""

    def test_returns_rows_within_date_range(self, in_memory_db):
        rows = ws.fetch_project_hours(
            in_memory_db, "2026-03-01", "2026-03-03"
        )
        assert len(rows) > 0

    def test_excludes_empty_project_id(self, in_memory_db):
        rows = ws.fetch_project_hours(
            in_memory_db, "2026-03-01", "2026-03-03"
        )
        project_ids = [r[0] for r in rows]
        assert "" not in project_ids

    def test_excludes_null_project_id(self, in_memory_db):
        rows = ws.fetch_project_hours(
            in_memory_db, "2026-03-01", "2026-03-03"
        )
        project_ids = [r[0] for r in rows]
        assert None not in project_ids

    def test_aggregates_hours_for_same_project(self, in_memory_db):
        rows = ws.fetch_project_hours(
            in_memory_db, "2026-03-01", "2026-03-03"
        )
        row_dict = {r[0]: r[2] for r in rows}
        # Project 0100 has 2.0 + 1.5 = 3.5 hours
        assert abs(row_dict["0100"] - 3.5) < 0.001

    def test_empty_result_for_out_of_range_dates(self, in_memory_db):
        rows = ws.fetch_project_hours(
            in_memory_db, "2020-01-01", "2020-01-31"
        )
        assert rows == []

    def test_single_day_range(self, in_memory_db):
        rows = ws.fetch_project_hours(
            in_memory_db, "2026-03-01", "2026-03-01"
        )
        # Only rows from March 1
        assert all(r[2] > 0 for r in rows)

    def test_rows_ordered_by_project_id(self, in_memory_db):
        rows = ws.fetch_project_hours(
            in_memory_db, "2026-03-01", "2026-03-03"
        )
        ids = [r[0] for r in rows]
        assert ids == sorted(ids)

    def test_returns_three_element_tuples(self, in_memory_db):
        rows = ws.fetch_project_hours(
            in_memory_db, "2026-03-01", "2026-03-03"
        )
        for row in rows:
            assert len(row) == 3


# ── print_org_table() ─────────────────────────────────────────

class TestPrintOrgTable:
    """Test org-mode table output."""

    def _capture(self, rows, cat_totals, grand, start, end):
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            ws.print_org_table(rows, cat_totals, grand, start, end)
            return mock_out.getvalue()

    def test_caption_present(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-07"
        )
        assert "#+CAPTION:" in out
        assert "2026-03-01" in out

    def test_booktabs_attribute(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-07"
        )
        assert "#+ATTR_LATEX: :booktabs t :center t" in out

    def test_header_row_present(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-07"
        )
        assert "Project ID" in out
        assert "Project Directory" in out
        assert "Hours" in out

    def test_project_rows_present(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-07"
        )
        assert "rna_crystal_ms" in out
        assert "100" in out

    def test_grand_total_present(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-07"
        )
        assert "Grand Total" in out
        assert "17.00" in out

    def test_category_subtotals_present(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-07"
        )
        assert "Manuscripts" in out
        assert "6.50" in out

    def test_zero_category_omitted(self):
        rows = [("0100", "ms_proj", 1.0)]
        cat_totals = [("Manuscripts", 1.0), ("Grants", 0.0)]
        out = self._capture(rows, cat_totals, 1.0, "2026-03-01", "2026-03-07")
        lines = out.strip().split("\n")
        # Grants with 0.0 should not appear in the subtotal rows.
        subtotal_lines = [l for l in lines if "Grants" in l]
        assert len(subtotal_lines) == 0

    def test_empty_project_directory_handled(self):
        rows = [("0100", None, 1.0)]
        cat_totals = [("Manuscripts", 1.0)]
        out = self._capture(rows, cat_totals, 1.0, "2026-03-01", "2026-03-07")
        assert "100" in out

    def test_long_directory_name_truncated(self):
        long_name = "a" * 50
        rows = [("0100", long_name, 1.0)]
        cat_totals = [("Manuscripts", 1.0)]
        out = self._capture(rows, cat_totals, 1.0, "2026-03-01", "2026-03-07")
        # The name should be truncated to 28 characters.
        assert "a" * 28 in out
        assert "a" * 29 not in out

    def test_pipe_delimited_rows(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-07"
        )
        for line in out.strip().split("\n"):
            if line.startswith("#"):
                continue
            assert line.startswith("|")
            assert line.endswith("|")


# ── print_latex_table() ───────────────────────────────────────

class TestPrintLatexTable:
    """Test LaTeX table output."""

    def _capture(self, rows, cat_totals, grand, start, end):
        with patch("sys.stdout", new_callable=StringIO) as mock_out:
            ws.print_latex_table(rows, cat_totals, grand, start, end)
            return mock_out.getvalue()

    def test_begin_and_end_table(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-07"
        )
        assert "\\begin{table}" in out
        assert "\\end{table}" in out

    def test_booktabs_rules(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-07"
        )
        assert "\\toprule" in out
        assert "\\midrule" in out
        assert "\\bottomrule" in out

    def test_caption_present(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-07"
        )
        assert "\\caption{" in out
        assert "2026-03-01" in out

    def test_centering(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-07"
        )
        assert "\\centering" in out

    def test_underscores_escaped(self):
        rows = [("0100", "my_rna_project", 1.0)]
        cat_totals = [("Manuscripts", 1.0)]
        out = self._capture(rows, cat_totals, 1.0, "2026-03-01", "2026-03-07")
        assert "my\\_rna\\_project" in out
        # Raw underscore should not appear in a data row.
        data_lines = [l for l in out.split("\n") if "100" in l and "&" in l]
        for line in data_lines:
            # All underscores in directory names should be escaped.
            parts = line.split("&")
            dir_part = parts[1] if len(parts) > 1 else ""
            assert "_" not in dir_part.replace("\\_", "")

    def test_grand_total_bold(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-07"
        )
        assert "\\textbf{Grand Total}" in out

    def test_category_subtotals_bold(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-07"
        )
        assert "\\textbf{Manuscripts}" in out

    def test_empty_directory_handled(self):
        rows = [("0100", None, 1.0)]
        cat_totals = [("Manuscripts", 1.0)]
        out = self._capture(rows, cat_totals, 1.0, "2026-03-01", "2026-03-07")
        assert "\\end{table}" in out

    def test_row_terminator(self, sample_rows, sample_category_totals):
        out = self._capture(
            sample_rows, sample_category_totals, 17.0,
            "2026-03-01", "2026-03-07"
        )
        data_lines = [l for l in out.split("\n")
                      if "&" in l and "textbf" not in l
                      and "Project ID" not in l]
        for line in data_lines:
            assert line.rstrip().endswith("\\\\")


# ── main() ────────────────────────────────────────────────────

class TestWeeklyMain:
    """Integration tests for weeklySummary.main()."""

    def test_main_produces_org_and_latex(self, in_memory_db):
        with patch.object(ws, "DB_PATH", ":memory:"):
            with patch("weeklySummary.sqlite3.connect", return_value=in_memory_db):
                with patch("weeklySummary.datetime") as mock_dt:
                    mock_dt.now.return_value = datetime(2026, 3, 4)
                    mock_dt.side_effect = lambda *a, **k: datetime(*a, **k)
                    with patch("sys.stdout", new_callable=StringIO) as mock_out:
                        ws.main()
                        output = mock_out.getvalue()
        assert "#+CAPTION:" in output
        assert "\\begin{table}" in output

    def test_main_date_range_is_7_days(self):
        """Verify the date window spans exactly 7 days."""
        captured_args = []
        original_fetch = ws.fetch_project_hours

        def spy_fetch(conn, start_date, end_date):
            captured_args.append((start_date, end_date))
            return []

        conn = sqlite3.connect(":memory:")
        conn.execute("""
            CREATE TABLE zTimeSpent (
                DateDashed TEXT, ProjectID TEXT,
                ProjectDirectory TEXT, TimeHr REAL
            )
        """)

        with patch.object(ws, "DB_PATH", ":memory:"):
            with patch("weeklySummary.sqlite3.connect", return_value=conn):
                with patch.object(ws, "fetch_project_hours", side_effect=spy_fetch):
                    with patch("sys.stdout", new_callable=StringIO):
                        ws.main()

        start_str, end_str = captured_args[0]
        start = datetime.strptime(start_str, "%Y-%m-%d")
        end = datetime.strptime(end_str, "%Y-%m-%d")
        assert (end - start).days == 7
        conn.close()

    def test_main_empty_database(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("""
            CREATE TABLE zTimeSpent (
                DateDashed TEXT, ProjectID TEXT,
                ProjectDirectory TEXT, TimeHr REAL
            )
        """)
        with patch.object(ws, "DB_PATH", ":memory:"):
            with patch("weeklySummary.sqlite3.connect", return_value=conn):
                with patch("sys.stdout", new_callable=StringIO) as mock_out:
                    ws.main()
                    output = mock_out.getvalue()
        assert "Grand Total" in output
        assert "0.00" in output
        conn.close()
