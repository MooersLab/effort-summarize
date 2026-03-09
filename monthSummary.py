#!/opt/homebrew/bin/python3.11
"""Monthly time tracking summary.

Prompts for a month name and year, then queries the mytime.db
database and prints a per-project summary followed by category
totals in org-mode and LaTeX table formats.
"""

import calendar
import sqlite3
from datetime import datetime


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
    print("#+CAPTION: Monthly time summary for {} through {}".format(
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
    print("\\caption{{Monthly time summary for {} through {}}}".format(
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
    # Prompt for month and year.
    now = datetime.now()
    month_input = input(
        "Enter month name or number [default: {}]: ".format(
            now.strftime("%B"))
    ).strip()
    year_input = input(
        "Enter year [default: {}]: ".format(now.year)
    ).strip()

    # Parse month.
    if not month_input:
        month = now.month
    elif month_input.isdigit():
        month = int(month_input)
    else:
        # Accept full or abbreviated month names.
        month_input_lower = month_input.lower()
        match = None
        for i in range(1, 13):
            if (calendar.month_name[i].lower().startswith(month_input_lower)
                    or calendar.month_abbr[i].lower() == month_input_lower):
                match = i
                break
        if match is None:
            print("Could not recognise month: {}".format(month_input))
            return
        month = match

    # Parse year.
    year = int(year_input) if year_input else now.year

    last_day = calendar.monthrange(year, month)[1]
    start_date = "{:04d}-{:02d}-01".format(year, month)
    end_date = "{:04d}-{:02d}-{:02d}".format(year, month, last_day)

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
