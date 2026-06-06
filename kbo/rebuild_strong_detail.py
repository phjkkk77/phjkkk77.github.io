import csv
from pathlib import Path

BASE = Path(__file__).parent / "2025_정규시즌_한화_롯데" / "상대전_정리"


def read_csv(fname):
    """Read CSV and return list of dicts"""
    rows = []
    with open(BASE / fname, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def to_num(v):
    if not v or v == "-":
        return None
    try:
        return float(v.replace(",", ""))
    except:
        return None


def top5_hitters(rows):
    """Return top 5 hitters by AVG"""
    valid = [r for r in rows if to_num(r.get("AVG")) is not None]
    valid.sort(key=lambda r: (to_num(r.get("AVG")) or -1, to_num(r.get("PA")) or -1), reverse=True)
    return valid[:5]


def pick_starter(rows):
    """Pick best ERA pitcher with GS > 0, else best ERA pitcher"""
    with_era = [r for r in rows if to_num(r.get("ERA")) is not None]
    starters = [r for r in with_era if to_num(r.get("GS") or "0") > 0]
    pool = starters if starters else with_era
    if not pool:
        return None
    pool.sort(key=lambda r: to_num(r.get("ERA")) or 999)
    return pool[0]


def build_strong_rows(team, opponent, hit_csv, pit_csv):
    """Build strong player rows from vs-opponent CSVs"""
    hitters = read_csv(hit_csv)
    pitchers = read_csv(pit_csv)

    rows = []
    for h in top5_hitters(hitters):
        rows.append(
            {
                "구분": "타자",
                "상대팀": opponent,
                "선수명": h.get("선수명", ""),
                "팀명": team,
                "PA": h.get("PA", ""),
                "H": h.get("H", ""),
                "HR": h.get("HR", ""),
                "AVG": h.get("AVG", ""),
                "ERA": "",
                "IP": "",
                "SO": "",
                "GS": "",
                "비고": "2025 상대팀별 타율 TOP5",
            }
        )

    starter = pick_starter(pitchers)
    if starter:
        rows.append(
            {
                "구분": "투수",
                "상대팀": opponent,
                "선수명": starter.get("선수명", ""),
                "팀명": team,
                "PA": "",
                "H": "",
                "HR": "",
                "AVG": "",
                "ERA": starter.get("ERA", ""),
                "IP": starter.get("IP", ""),
                "SO": starter.get("SO", ""),
                "GS": starter.get("GS", ""),
                "비고": "선발투수 1명 (2025 상대팀별)",
            }
        )

    return rows


def write_csv(fname, rows):
    """Write CSV with all rows"""
    if not rows:
        print(f"No data for {fname}")
        return
    headers = ["구분", "상대팀", "선수명", "팀명", "PA", "H", "HR", "AVG", "ERA", "IP", "SO", "GS", "비고"]
    with open(BASE / fname, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in headers})
    print(f"✓ {fname}: {len(rows)} rows")


# Rebuild both strong files from existing vs-opponent CSVs
rows_hh = build_strong_rows("한화", "롯데", "2025_한화_타자_vs_롯데.csv", "2025_한화_투수_vs_롯데.csv")
rows_lt = build_strong_rows("롯데", "한화", "2025_롯데_타자_vs_한화.csv", "2025_롯데_투수_vs_한화.csv")

write_csv("2025_한화_강자_세부.csv", rows_hh)
write_csv("2025_롯데_강자_세부.csv", rows_lt)
