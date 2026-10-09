"""Export every table of the database to CSV files (open them in Excel) and print a short summary.

Run from the project folder:   python -m backend.export_data
Files are written to the 'exports' folder. Password hashes are NOT exported.
"""
import csv
import json
from pathlib import Path
from sqlalchemy import inspect, text
from .app.database import engine

OUT = Path(__file__).resolve().parents[1] / "exports"
SKIP_COLUMNS = {"password_hash"}


def main():
    OUT.mkdir(exist_ok=True)
    insp = inspect(engine)
    with engine.connect() as conn:
        for table in sorted(insp.get_table_names()):
            cols = [c["name"] for c in insp.get_columns(table) if c["name"] not in SKIP_COLUMNS]
            rows = conn.execute(text(f'SELECT {", ".join(cols)} FROM {table}')).fetchall()
            with open(OUT / f"{table}.csv", "w", newline="", encoding="utf-8-sig") as f:      # utf-8-sig so Excel shows Hindi correctly
                w = csv.writer(f)
                w.writerow(cols)
                for r in rows:
                    w.writerow([json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for v in r])
            print(f"{table:<16} {len(rows):>6} rows  ->  exports/{table}.csv")
        print("\nUsers by role:")
        for role, n in conn.execute(text("SELECT role, COUNT(*) FROM users GROUP BY role")):
            print(f"  {role:<8} {n}")
        print("Complaints by status:")
        for st, n in conn.execute(text("SELECT status, COUNT(*) FROM complaints GROUP BY status")):
            print(f"  {st:<12} {n}")


if __name__ == "__main__":
    main()
