import csv
from pathlib import Path

BASE = Path(__file__).parent / "2025_정규시즌_한화_롯데" / "상대전_정리"

def read_csv(filename):
    """Read CSV file and return list of dicts"""
    path = BASE / filename
    with open(path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return list(reader)

def safe_float(val, default=0):
    """Safely convert to float, handling '-' and empty strings"""
    if not val or val == '-':
        return default
    try:
        return float(val)
    except ValueError:
        return default

def get_top_batters(csv_file, team_name, opponent):
    """Extract top 5 batters from CSV"""
    data = read_csv(csv_file)
    top = []
    for row in data:
        top.append({
            "구분": "타자",
            "팀": team_name,
            "상대팀": opponent,
            "선수명": row.get("선수명", ""),
            "AVG": row.get("AVG", ""),
            "HR": row.get("HR", ""),
            "RBI": row.get("RBI", ""),
        })
    # Sort by AVG (타율)
    return sorted(top, key=lambda x: safe_float(x["AVG"], 0), reverse=True)[:5]

def get_top_pitchers(csv_file, team_name, opponent):
    """Extract pitchers from CSV"""
    data = read_csv(csv_file)
    top = []
    for row in data:
        top.append({
            "구분": "투수",
            "팀": team_name,
            "상대팀": opponent,
            "선수명": row.get("선수명", ""),
            "H": row.get("H", ""),
            "BB": row.get("BB", ""),
            "SO": row.get("SO", ""),
        })
    # Sort by SO (삼진) - higher is better
    return sorted(top, key=lambda x: safe_float(x["SO"], 0), reverse=True)[:5]

# Collect all strong players
strong_players = []

# 한화 타자 vs 롯데
print("한화 타자 vs 롯데...")
strong_players.extend(get_top_batters("2025_한화_타자_vs_롯데.csv", "한화", "롯데"))

# 한화 투수 vs 롯데
print("한화 투수 vs 롯데...")
strong_players.extend(get_top_pitchers("2025_한화_투수_vs_롯데.csv", "한화", "롯데"))

# 롯데 타자 vs 한화
print("롯데 타자 vs 한화...")
strong_players.extend(get_top_batters("2025_롯데_타자_vs_한화.csv", "롯데", "한화"))

# 롯데 투수 vs 한화
print("롯데 투수 vs 한화...")
strong_players.extend(get_top_pitchers("2025_롯데_투수_vs_한화.csv", "롯데", "한화"))

# Write to CSV
output_path = BASE / "강자_세부.csv"
if strong_players:
    # Get all unique fieldnames
    all_fieldnames = set()
    for row in strong_players:
        all_fieldnames.update(row.keys())
    fieldnames = ["팀", "상대팀", "선수명", "세부카테고리"] + [f for f in all_fieldnames if f not in ["팀", "상대팀", "선수명", "세부카테고리"]]
    
    with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(strong_players)
    print(f"\n✓ 강자_세부.csv 생성 완료 ({len(strong_players)} rows)")
else:
    print("오류: 강자 데이터를 생성할 수 없습니다.")

