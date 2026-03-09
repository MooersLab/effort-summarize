"""Shared fixtures for weeklySummary and monthSummary tests."""

import sqlite3
import pytest


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database with the zTimeSpent schema
    and sample data spanning multiple categories and dates."""
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE zTimeSpent (
            DateDashed   TEXT,
            ProjectID    TEXT,
            ProjectDirectory TEXT,
            TimeHr       REAL
        )
    """)
    sample_rows = [
        # Manuscripts
        ("2026-03-01", "0100", "rna_crystal_ms",     2.0),
        ("2026-03-02", "0100", "rna_crystal_ms",     1.5),
        ("2026-03-01", "0436", "quantum_rna_ms",     3.0),
        # Grants
        ("2026-03-01", "1001", "nih_r01_grant",      4.0),
        # Books
        ("2026-03-03", "2001", "pymol_book",         1.0),
        # Talks
        ("2026-03-01", "3283", "datasci_talk",       2.5),
        # Posters
        ("2026-03-02", "4010", "aca_poster",         1.0),
        # Software Repositories
        ("2026-03-01", "4200", "whisper_dvr",        2.0),
        # Manuscript Reviews
        ("2026-03-03", "5010", "acta_cryst_review",  1.5),
        # Private (first sub-range 6000-6299)
        ("2026-03-01", "6001", "personal_admin",     0.5),
        # Lab Related (6300-6599)
        ("2026-03-01", "6350", "lab_inventory",      1.0),
        # Private (second sub-range 6600-6619)
        ("2026-03-02", "6610", "personal_finance",   0.5),
        # Lab Related (6620-6630)
        ("2026-03-02", "6625", "lab_safety_train",   1.0),
        # Private (third sub-range 6631-6899)
        ("2026-03-03", "6700", "personal_reading",   0.5),
        # Lab Related (6900-6999)
        ("2026-03-03", "6950", "lab_equipment",      2.0),
        # Service
        ("2026-03-01", "7010", "dept_committee",     1.0),
        # Teaching
        ("2026-03-02", "8100", "bioc_6463",          3.0),
        # Workshops
        ("2026-03-03", "9100", "okla_datasci_wkshp", 2.0),
        # Edge cases: empty and NULL ProjectID rows
        ("2026-03-01", "",     "empty_proj",         0.25),
        ("2026-03-01", None,   "null_proj",          0.25),
        # Edge case: ProjectID outside all ranges
        ("2026-03-01", "4000", "orphan_proj",        0.5),
    ]
    conn.executemany(
        "INSERT INTO zTimeSpent VALUES (?, ?, ?, ?)", sample_rows
    )
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def sample_rows():
    """Pre-built row tuples as returned by fetch_project_hours."""
    return [
        ("0100", "rna_crystal_ms",    3.5),
        ("0436", "quantum_rna_ms",    3.0),
        ("1001", "nih_r01_grant",     4.0),
        ("3283", "datasci_talk",      2.5),
        ("6350", "lab_inventory",     1.0),
        ("8100", "bioc_6463",         3.0),
    ]


@pytest.fixture
def sample_category_totals():
    """Pre-built category totals list for table printing tests."""
    return [
        ("Manuscripts",   6.5),
        ("Grants",        4.0),
        ("Talks",         2.5),
        ("Lab Related",   1.0),
        ("Teaching",      3.0),
    ]
