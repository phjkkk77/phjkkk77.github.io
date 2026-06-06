import csv
import html
import re
import http.cookiejar
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

BASE = "https://www.koreabaseball.com"
HITTER_URL = f"{BASE}/Record/Player/HitterBasic/Basic1.aspx"
PITCHER_URL = f"{BASE}/Record/Player/PitcherBasic/Basic1.aspx"

FORM_PREFIX = "ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$"

FIELDS = {
    "season": FORM_PREFIX + "ddlSeason$ddlSeason",
    "series": FORM_PREFIX + "ddlSeries$ddlSeries",
    "team": FORM_PREFIX + "ddlTeam$ddlTeam",
    "pos": FORM_PREFIX + "ddlPos$ddlPos",
    "situation": FORM_PREFIX + "ddlSituation$ddlSituation",
    "detail": FORM_PREFIX + "ddlSituationDetail$ddlSituationDetail",
}

TEAM_CODE = {"한화": "HH", "롯데": "LT"}

OUT_DIR = Path(__file__).resolve().parent / "2025_정규시즌_한화_롯데" / "상대전_정리"
OUT_DIR.mkdir(parents=True, exist_ok=True)

COOKIE_JAR = http.cookiejar.CookieJar()
OPENER = build_opener(HTTPCookieProcessor(COOKIE_JAR))


TAG_RE = re.compile(r"<[^>]+>")
HIDDEN_RE = re.compile(r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"', re.I)
SELECT_RE_TMPL = r'<select[^>]*name="%s"[^>]*>(.*?)</select>'
OPTION_RE = re.compile(r'<option[^>]*value="([^"]*)"[^>]*>(.*?)</option>', re.I | re.S)
TABLE_RE = re.compile(r"<table[^>]*>(.*?)</table>", re.I | re.S)
THEAD_RE = re.compile(r"<thead[^>]*>(.*?)</thead>", re.I | re.S)
TBODY_RE = re.compile(r"<tbody[^>]*>(.*?)</tbody>", re.I | re.S)
TR_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.I | re.S)
TH_RE = re.compile(r"<th[^>]*>(.*?)</th>", re.I | re.S)
TD_RE = re.compile(r"<td[^>]*>(.*?)</td>", re.I | re.S)
POSTBACK_RE = re.compile(r"__doPostBack\('([^']+)'\s*,\s*''\)")


def http_get(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with OPENER.open(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def http_post(url: str, data: dict[str, str]) -> str:
    payload = urlencode(data).encode("utf-8")
    req = Request(
        url,
        data=payload,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": BASE,
            "Referer": url,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with OPENER.open(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def clean_text(raw: str) -> str:
    text = TAG_RE.sub("", raw)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_hidden(html_text: str) -> dict[str, str]:
    return {name: html.unescape(value) for name, value in HIDDEN_RE.findall(html_text)}


def parse_select_options(html_text: str, field_name: str) -> list[tuple[str, str]]:
    pattern = SELECT_RE_TMPL % re.escape(field_name)
    m = re.search(pattern, html_text, re.I | re.S)
    if not m:
        return []
    block = m.group(1)
    return [(v, clean_text(t)) for v, t in OPTION_RE.findall(block)]


def pick_option_value(options: list[tuple[str, str]], target_text: str) -> str:
    norm_target = re.sub(r"\s+", "", target_text)
    for value, text in options:
        if text == target_text:
            return value
    for value, text in options:
        norm_text = re.sub(r"\s+", "", text)
        if norm_target in norm_text:
            return value
    sample = ", ".join(text for _, text in options[:20])
    raise ValueError(f"Option text not found: {target_text}. available={sample}")


def pick_regular_series(options: list[tuple[str, str]]) -> str:
    for value, text in options:
        if "정규" in text:
            return value
    raise ValueError("정규시즌 옵션을 찾지 못했습니다.")


def parse_table(html_text: str) -> tuple[list[str], list[dict[str, str]]]:
    tables = TABLE_RE.findall(html_text)
    for table in tables:
        if "기록이 없습니다" in table:
            continue

        headers: list[str] = []
        rows: list[dict[str, str]] = []

        thead_match = THEAD_RE.search(table)
        tbody_match = TBODY_RE.search(table)

        if thead_match and tbody_match:
            headers = [clean_text(x) for x in TH_RE.findall(thead_match.group(1))]
            body_rows = TR_RE.findall(tbody_match.group(1))
        else:
            # Some KBO pages omit explicit thead/tbody blocks.
            tr_all = TR_RE.findall(table)
            if not tr_all:
                continue
            headers = [clean_text(x) for x in TH_RE.findall(tr_all[0])]
            body_rows = tr_all[1:]

        if not headers or "선수명" not in headers:
            continue

        for tr in body_rows:
            tds = [clean_text(x) for x in TD_RE.findall(tr)]
            if len(tds) != len(headers):
                continue
            row = {headers[i]: tds[i] for i in range(len(headers))}
            rows.append(row)

        if rows:
            return headers, rows

    return [], []


def collect_all_pages(url: str, initial_data: dict[str, str]) -> tuple[list[str], list[dict[str, str]]]:
    html_text = http_post(url, initial_data)
    headers, rows = parse_table(html_text)

    if not rows:
        debug_name = "debug_hitter_response.html" if "HitterBasic" in url else "debug_pitcher_response.html"
        (OUT_DIR / debug_name).write_text(html_text, encoding="utf-8")

    page_targets = sorted(
        set(t for t in POSTBACK_RE.findall(html_text) if "ucPager$btnNo" in t),
        key=lambda x: int(re.search(r"btnNo(\d+)", x).group(1)),
    )

    current_html = html_text
    all_rows = list(rows)

    for target in page_targets:
        hidden = parse_hidden(current_html)
        form = {
            "__EVENTTARGET": target,
            "__EVENTARGUMENT": "",
            **hidden,
            **initial_data,
        }
        current_html = http_post(url, form)
        _, page_rows = parse_table(current_html)
        all_rows.extend(page_rows)

    seen = set()
    deduped = []
    for r in all_rows:
        key = tuple(r.get(k, "") for k in ["선수명", "팀명", "AVG", "ERA", "IP", "PA", "H", "SO", "GS"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(r)

    return headers, deduped


def build_initial_form(url: str, team_name: str, opp_name: str) -> dict[str, str]:
    html_text = http_get(url)
    hidden = parse_hidden(html_text)

    season_opts = parse_select_options(html_text, FIELDS["season"])
    series_opts = parse_select_options(html_text, FIELDS["series"])
    team_opts = parse_select_options(html_text, FIELDS["team"])
    pos_opts = parse_select_options(html_text, FIELDS["pos"])
    situ_opts = parse_select_options(html_text, FIELDS["situation"])

    season_val = pick_option_value(season_opts, "2025")
    series_val = pick_regular_series(series_opts)
    team_val = pick_option_value(team_opts, team_name)
    pos_val = pos_opts[0][0] if pos_opts else ""
    situ_val = pick_option_value(situ_opts, "상대팀별")

    # Step 1: trigger situation dropdown postback so situation-detail options are populated.
    first_form = {
        "__EVENTTARGET": FIELDS["situation"],
        "__EVENTARGUMENT": "",
        **hidden,
        FIELDS["season"]: season_val,
        FIELDS["series"]: series_val,
        FIELDS["team"]: team_val,
        FIELDS["pos"]: pos_val,
        FIELDS["situation"]: situ_val,
        FIELDS["detail"]: "",
    }
    after_situation = http_post(url, first_form)
    hidden2 = parse_hidden(after_situation)
    detail_opts = parse_select_options(after_situation, FIELDS["detail"])
    detail_val = pick_option_value(detail_opts, opp_name)

    return {
        "__EVENTTARGET": "",
        "__EVENTARGUMENT": "",
        **hidden2,
        FIELDS["season"]: season_val,
        FIELDS["series"]: series_val,
        FIELDS["team"]: team_val,
        FIELDS["pos"]: pos_val,
        FIELDS["situation"]: situ_val,
        FIELDS["detail"]: detail_val,
    }


def write_csv(path: Path, headers: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore", quoting=csv.QUOTE_ALL)
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in headers})


def to_num(text: str) -> float | None:
    t = (text or "").replace(",", "").strip()
    if t in {"", "-"}:
        return None
    try:
        return float(t)
    except ValueError:
        return None


def ip_to_outs(ip_text: str) -> int:
    if not ip_text:
        return 0
    parts = ip_text.strip().split()
    try:
        whole = int(parts[0])
    except ValueError:
        return 0
    outs = whole * 3
    if len(parts) > 1:
        if parts[1] == "1/3":
            outs += 1
        elif parts[1] == "2/3":
            outs += 2
    return outs


def top5_hitters(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    valid = [r for r in rows if to_num(r.get("AVG", "")) is not None]
    valid.sort(key=lambda r: (to_num(r.get("AVG", "")) or -1, to_num(r.get("PA", "")) or -1), reverse=True)
    return valid[:5]


def pick_starter(rows: list[dict[str, str]]) -> dict[str, str] | None:
    with_era = [r for r in rows if to_num(r.get("ERA", "")) is not None]
    starters = [r for r in with_era if (to_num(r.get("GS", "")) or 0) > 0]
    pool = starters if starters else with_era
    if not pool:
        return None
    pool.sort(key=lambda r: (to_num(r.get("ERA", "")) or 999, -(ip_to_outs(r.get("IP", "")))))
    return pool[0]


def build_strong_rows(team: str, opponent: str, hit_rows: list[dict[str, str]], pit_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    result = []

    for h in top5_hitters(hit_rows):
        result.append(
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
                "비고": "2025 정규시즌 상대팀별 타자 TOP5",
            }
        )

    starter = pick_starter(pit_rows)
    if starter:
        result.append(
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
                "비고": "2025 정규시즌 상대팀별 선발투수 1명 (GS>0 우선)",
            }
        )

    return result


def rebuild_for_team(team: str, opponent: str) -> None:
    hit_form = build_initial_form(HITTER_URL, team, opponent)
    pit_form = build_initial_form(PITCHER_URL, team, opponent)

    hit_headers, hit_rows = collect_all_pages(HITTER_URL, hit_form)
    pit_headers, pit_rows = collect_all_pages(PITCHER_URL, pit_form)

    if not hit_rows:
        raise RuntimeError(f"타자 데이터가 비어 있습니다: {team} vs {opponent}")
    if not pit_rows:
        raise RuntimeError(f"투수 데이터가 비어 있습니다: {team} vs {opponent}")

    write_csv(OUT_DIR / f"2025_{team}_타자_vs_{opponent}.csv", hit_headers, hit_rows)
    write_csv(OUT_DIR / f"2025_{team}_투수_vs_{opponent}.csv", pit_headers, pit_rows)

    strong_headers = ["구분", "상대팀", "선수명", "팀명", "PA", "H", "HR", "AVG", "ERA", "IP", "SO", "GS", "비고"]
    strong_rows = build_strong_rows(team, opponent, hit_rows, pit_rows)
    write_csv(OUT_DIR / f"2025_{team}_강자_세부.csv", strong_headers, strong_rows)

    print(f"[OK] {team} vs {opponent}: 타자 {len(hit_rows)}행, 투수 {len(pit_rows)}행, 강자 {len(strong_rows)}행")


def main() -> None:
    rebuild_for_team("한화", "롯데")
    rebuild_for_team("롯데", "한화")


if __name__ == "__main__":
    main()
