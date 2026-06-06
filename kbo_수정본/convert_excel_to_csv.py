import csv
from pathlib import Path
import openpyxl

BASE = Path(__file__).parent / "2025_정규시즌_한화_롯데" / "상대전_정리"

# Excel to CSV mapping
mappings = [
    ("롯데상대 한화타자들 기록.xlsx", "2025_한화_타자_vs_롯데.csv"),
    ("롯데상대 한화투수들 기록.xlsx", "2025_한화_투수_vs_롯데.csv"),
    ("한화상대 롯데타자들 기록.xlsx", "2025_롯데_타자_vs_한화.csv"),
    ("한화상대 롯데투수들 기록.xlsx", "2025_롯데_투수_vs_한화.csv"),
]


def excel_to_csv(xlsx_file, csv_file):
    """Convert Excel file to CSV"""
    xlsx_path = BASE / xlsx_file
    csv_path = BASE / csv_file
    
    # Load workbook
    wb = openpyxl.load_workbook(xlsx_path)
    ws = wb.active
    
    # Read all rows
    rows = []
    headers = None
    for idx, row in enumerate(ws.iter_rows(values_only=True)):
        if idx == 0:
            headers = [str(v) if v is not None else "" for v in row]
        else:
            rows.append({headers[i]: (str(row[i]) if row[i] is not None else "") for i in range(len(headers))})
    
    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    
    print(f"✓ {xlsx_file} → {csv_file} ({len(rows)} rows)")


for xlsx, csv_name in mappings:
    excel_to_csv(xlsx, csv_name)
