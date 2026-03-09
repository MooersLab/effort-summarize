![Version](https://img.shields.io/static/v1?label=effort-summary&message=0.1.0&color=brightcolor)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)


# Time-Tracking Summary Scripts

Two command-line tools that query a personal SQLite time-tracking database
(`mytime.db`) and print per-project and per-category summaries in both
**org-mode** and **LaTeX** table formats.

| Script | Purpose |
|---|---|
| `weeklySummary.py` | Summarises the past 7 days (non-interactive) |
| `monthSummary.py`  | Summarises a user-selected calendar month     |

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Database Schema](#database-schema)
4. [Configuration](#configuration)
5. [Usage](#usage)
6. [Output Formats](#output-formats)
7. [Project Categories](#project-categories)
8. [Running the Tests](#running-the-tests)
9. [Coverage Reports](#coverage-reports)
10. [Troubleshooting](#troubleshooting)
11. [License](#license)

---

## Prerequisites

- **Python 3.9+** (tested with 3.11 on macOS via Homebrew)
- The Python standard library modules `sqlite3`, `calendar`, and `datetime`
  (no third-party runtime dependencies)
- For testing: `pytest` and `coverage`

## Installation

### 1. Clone or copy the scripts

Place the following files in the same directory as your database (or any
directory on your `PATH`):

```
weeklySummary.py
monthSummary.py
```

### 2. Make them executable (macOS / Linux)

```bash
chmod +x weeklySummary.py monthSummary.py
```

### 3. Install test dependencies (optional)

```bash
pip install pytest coverage
```

Or, if you prefer to keep your system Python clean:

```bash
python3 -m pip install --user pytest coverage
```

### 4. Verify the installation

```bash
python3 weeklySummary.py          # prints the past-7-day summary
python3 monthSummary.py           # prompts for month and year
make test                         # runs the test suite
```

---

## Database Schema

Both scripts query a table called **`zTimeSpent`** in a SQLite database.
The expected columns are:

| Column             | Type  | Description                          |
|---|---|---|
| `DateDashed`       | TEXT  | Date in `YYYY-MM-DD` format          |
| `ProjectID`        | TEXT  | Numeric project code stored as text  |
| `ProjectDirectory` | TEXT  | Human-readable project folder name   |
| `TimeHr`           | REAL  | Hours spent (decimal)                |

Rows with empty or `NULL` values for `ProjectID` are automatically excluded
from the reports.

---

## Configuration

Both scripts contain a single configuration variable near the top of the
file:

```python
DB_PATH = "/Users/blaine/6003TimeTracking/cb/mytime.db"
```

Change this to the absolute path of your own `mytime.db` file.

---

## Usage

### Weekly summary

```bash
./weeklySummary.py
```

No arguments or prompts.  The script computes the date range from
**today minus 7 days** through **today**, queries the database, and prints
two tables (org-mode then LaTeX) to standard output.

**Tip — redirect to a file for later pasting into Emacs:**

```bash
./weeklySummary.py > weekly_report.org
```

### Monthly summary

```bash
./monthSummary.py
```

The script prompts for two values:

```
Enter month name or number [default: March]: February
Enter year [default: 2026]: 2025
```

Accepted month formats:

| Input         | Interpretation |
|---|---|
| `3`           | March          |
| `March`       | March          |
| `Mar`         | March          |
| `mar`         | March          |
| *(empty)*     | Current month  |

If you press **Enter** without typing anything, the current month and
current year are used.

**Tip — pipe through `pbcopy` on macOS to copy the tables to the
clipboard:**

```bash
./monthSummary.py | pbcopy
```

---

## Output Formats

Each script prints two consecutive tables to standard output.

### Org-mode table

```
#+CAPTION: Weekly time summary for 2026-03-01 through 2026-03-08
#+ATTR_LATEX: :booktabs t :center t
| Project ID | Project Directory             | Hours |
|------------+------------------------------+-------|
|        100 | rna_crystal_ms               |  3.50 |
|        436 | quantum_rna_ms               |  3.00 |
|       1001 | nih_r01_grant                |  4.00 |
|------------+------------------------------+-------|
|            | Manuscripts                  |  6.50 |
|            | Grants                       |  4.00 |
|------------+------------------------------+-------|
|            | Grand Total                  | 10.50 |
|------------+------------------------------+-------|
```

### LaTeX table

```latex
\begin{table}[htbp]
\centering
\caption{Weekly time summary for 2026-03-01 through 2026-03-08}
\begin{tabular}{rlr}
\toprule
Project ID & Project Directory & Hours \\
\midrule
100 & rna\_crystal\_ms & 3.50 \\
436 & quantum\_rna\_ms & 3.00 \\
1001 & nih\_r01\_grant & 4.00 \\
\midrule
 & \textbf{Manuscripts} & \textbf{6.50} \\
 & \textbf{Grants} & \textbf{4.00} \\
\midrule
 & \textbf{Grand Total} & \textbf{10.50} \\
\bottomrule
\end{tabular}
\end{table}
```

The LaTeX table uses the `booktabs` package and escapes underscores in
directory names.  Category subtotals and the grand total are set in
`\textbf{}`.

---

## Project Categories

Projects are classified by their numeric `ProjectID` ranges:

| Category              | ID Range      |
|---|---|
| Manuscripts           | 1 – 999       |
| Grants                | 1000 – 1999   |
| Books                 | 2000 – 2999   |
| Talks                 | 3000 – 3999   |
| Posters               | 4001 – 4150   |
| Software Repositories | 4151 – 4999   |
| Manuscript Reviews    | 5000 – 5999   |
| Private               | 6000 – 6299, 6600 – 6619, 6631 – 6899 |
| Lab Related           | 6300 – 6599, 6620 – 6630, 6900 – 6999 |
| Service               | 7000 – 7999   |
| Teaching              | 8000 – 8999   |
| Workshops             | 9000 – 9999   |

Projects with IDs falling outside all defined ranges (for example, 0 or
4000) are reported under **Uncategorized**.

To add or modify categories, edit the `CATEGORIES` list at the top of each
script.  The `CATEGORY_NAMES` list is derived automatically.

---

## Running the Tests

### Prerequisites

```bash
pip install pytest coverage
```

### Run all tests

```bash
make test
```

or equivalently:

```bash
python3 -m pytest -v test_weeklySummary.py test_monthSummary.py
```

### What the tests cover

The test suite (`test_weeklySummary.py`, `test_monthSummary.py`, and the
shared `conftest.py` fixtures) covers:

- **Category configuration** — validates that ranges do not overlap, that
  `CATEGORY_NAMES` is properly deduplicated, and both scripts define
  identical categories.
- **`category_for()`** — parametrised tests for every category boundary,
  every Lab Related / Private sub-range boundary, and edge cases (empty
  string, `None`, non-numeric input, integer input, out-of-range IDs).
- **`fetch_project_hours()`** — uses an in-memory SQLite database to verify
  date filtering, aggregation, ordering, and exclusion of empty/null
  `ProjectID` values.
- **`print_org_table()`** — captures stdout and checks for the `#+CAPTION`
  line, `#+ATTR_LATEX` line, pipe-delimited rows, category subtotals, the
  grand total, zero-category omission, `None` directory handling, and
  truncation of long directory names.
- **`print_latex_table()`** — checks for `\begin{table}` / `\end{table}`,
  booktabs rules, `\centering`, `\caption`, underscore escaping, bold
  subtotals, and row terminators.
- **`main()` (weekly)** — integration tests with a mocked database verifying
  that both org and LaTeX output appear, that the date range spans exactly
  7 days, and that an empty database produces a valid `0.00` grand total.
- **`main()` (monthly)** — tests for full month names, abbreviations, partial
  names, numeric input, case insensitivity, default values (pressing Enter),
  leap year / non-leap-year February handling, invalid month names, and full
  integration with sample data, including Lab Related and Uncategorized
  subtotals.

---

## Coverage Reports

### Terminal report

```bash
make coverage
```

This runs the tests under `coverage`, then prints a line-by-line coverage
summary.

### HTML report

```bash
make coverage-html
```

This generates an interactive report in `htmlcov/index.html` that you can
open in a browser.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'pytest'` | `pytest` is not installed | `pip install pytest` |
| `sqlite3.OperationalError: no such table: zTimeSpent` | Wrong database path | Update `DB_PATH` in the script |
| `TypeError: '<=' not supported between instances of 'int' and 'str'` | Running an older version of the script | Ensure you are using the latest version with `int()` casting in `category_for()` |
| `ValueError: invalid literal for int()` | Empty `ProjectID` rows in the database | The current scripts filter these out; update if still occurring |
| Empty report (all zeros) | No data in the requested date range | Try a different month/week, or check `DateDashed` format in the database |

---

## Status

- Works as advertised.
- Passes all tests.
- 99% coverage.

## License

MIT licnense. These scripts are provided for personal use.  Modify and distribute as needed.


## Update table


| Version | Changes                                                                                                                | Date              |
|:---------|:------------------------------------------------------------------------------------------------------------------------|:-------------------|
|   0.1.0   | Initiate project. Added badges, funding, and this update table.                                                        | 2026 March 8 |

## Sources of funding

- NIH: R01 CA242845
- NIH: R01 AI088011
- NIH: P30 CA225520 (PI: R. Mannel)
- NIH: P20 GM103640 and P30 GM145423 (PI: A. West)
