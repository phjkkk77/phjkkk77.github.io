import csv
from pathlib import Path

BASE = Path(__file__).parent / "2025_정규시즌_한화_롯데" / "상대전_정리"

# Read the combined strong players file
result = {}
with open(BASE / "강자_세부.csv", "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        team = row.get("팀", "")
        if team not in result:
            result[team] = []
        result[team].append(row)

# Write separate files for each team
for team, players in result.items():
    output_filename = f"2025_{team}_강자_세부.csv"
    output_path = BASE / output_filename
    
    if players:
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = players[0].keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(players)
        print(f"✓ {output_filename} ({len(players)} rows)")
