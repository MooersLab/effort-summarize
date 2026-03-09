#!/opt/homebrew/bin/python3.11
"""Weekly time tracking summary.

Queries the mytime.db database for the past 7 days and prints
a per-project summary followed by category totals in org-mode
and LaTeX table formats.
"""

import sqlite3
from datetime import datetime, timedelta


# ── configuration ──────────────────────────────────────────────
DB_PATH = "/Users/blaine/6003TimeTracking/cb/mytime.db"

CATEGORIES = [
    ("Manuscripts",            1,    999),
    ("Grants",              1000,   1999),
    ("Books",               2000,   2999),
    ("Talks",               3000,   3999),
    ("Posters",             4001,   4150),
    ("Software Repositories", 4151, 4999),
    ("Manuscript Reviews",  5000,   5999),
    ("Private",             6000,   6299),
    ("Lab Related",         6300,   6599),
    ("Private",             6600,   6619),
    ("Lab Related",         6620,   6630),
    ("Private",             6631,   6899),
    ("Lab Related",         6900,   6999),
    ("Service",             7000,   7999),
    ("Teaching",            8000,   8999),
    ("Workshops",           9000,   9999),
]

# Ordered unique category names for display.
CATEGORY_NAMES = list(dict.fromkeys(name for name, _, _ in CATEGORIES))


def fetch_project_hours(conn, start_date, end_date):
    """Return a list of (ProjectID, ProjectDirectory, total hours) for the date window."""
    query = """
        SELECT ProjectID, ProjectDirectory, SUM(TimeHr) AS TotalHr
        FROM zTimeSpent
        WHERE DateDashed BETWEEN ? AND ?
          AND ProjectID IS NOT NULL
          AND ProjectID != ''
        GROUP BY ProjectID, ProjectDirectory
        ORDER BY ProjectID
    """
    cursor = conn.execute(query, (start_date, end_date))
    return cursor.fetchall()


def category_for(project_id):
    """Return the category name for a given ProjectID, or 'Uncategorized'."""
    try:
        pid = int(project_id)
    except (ValueError, TypeError):
        return "Uncategorized"
    for name, lo, hi in CATEGORIES:
        if lo <= pid <= hi:
            return name
    return "Uncategorized"


def print_org_table(rows, category_totals, grand_total, start_date, end_date):
    """Print the results as an org-mode table with booktabs and caption."""
    print("#+CAPTION: Weekly time summary for {} through {}".format(
        start_date, end_date))
    print("#+ATTR_LATEX: :booktabs t :center t")
    print("| Project ID | Project Directory             | Hours |")
    print("|------------+------------------------------+-------|")
    for project_id, project_dir, hours in rows:
        name = project_dir if project_dir else ""
        print("| {:>10d} | {:<28s} | {:5.2f} |".format(
            int(project_id), name[:28], hours))
    print("|------------+------------------------------+-------|")

    # Category subtotals
    for name, total in category_totals:
        if total > 0:
            print("| {:<10s} | {:<28s} | {:5.2f} |".format("", name, total))
    print("|------------+------------------------------+-------|")
    print("| {:<10s} | {:<28s} | {:5.2f} |".format("", "Grand Total", grand_total))
    print("|------------+------------------------------+-------|")


def print_latex_table(rows, category_totals, grand_total, start_date, end_date):
    """Print the results as a LaTeX table with booktabs."""
    print("\\begin{table}[htbp]")
    print("\\centering")
    print("\\caption{{Weekly time summary for {} through {}}}".format(
        start_date, end_date))
    print("\\begin{tabular}{rlr}")
    print("\\toprule")
    print("Project ID & Project Directory & Hours \\\\")
    print("\\midrule")
    for project_id, project_dir, hours in rows:
        dname = project_dir if project_dir else ""
        # Escape underscores for LaTeX
        dname = dname.replace("_", "\\_")
        print("{} & {} & {:.2f} \\\\".format(int(project_id), dname, hours))
    print("\\midrule")

    # Category subtotals
    for name, total in category_totals:
        if total > 0:
            print(" & \\textbf{{{}}} & \\textbf{{{:.2f}}} \\\\".format(name, total))
    print("\\midrule")
    print(" & \\textbf{{Grand Total}} & \\textbf{{{:.2f}}} \\\\".format(grand_total))
    print("\\bottomrule")
    print("\\end{tabular}")
    print("\\end{table}")


def main():
    end_dt = datetime.now()
    start_dt = end_dt - timedelta(days=7)
    start_date = start_dt.strftime("%Y-%m-%d")
    end_date = end_dt.strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)

    rows = fetch_project_hours(conn, start_date, end_date)
    conn.close()

    # Build category totals from the per-project rows.
    cat_sums = {name: 0.0 for name in CATEGORY_NAMES}
    cat_sums["Uncategorized"] = 0.0

    for project_id, project_dir, hours in rows:
        cat_sums[category_for(project_id)] += hours

    grand_total = sum(hours for _, _, hours in rows)

    # Deduplicated category totals in display order.
    category_totals = [(name, cat_sums[name]) for name in CATEGORY_NAMES]
    if cat_sums["Uncategorized"] > 0:
        category_totals.append(("Uncategorized", cat_sums["Uncategorized"]))

    print_org_table(rows, category_totals, grand_total, start_date, end_date)
    print()
    print_latex_table(rows, category_totals, grand_total, start_date, end_date)


if __name__ == "__main__":
    main()
