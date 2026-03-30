import re
import html
import http.cookiejar
from urllib.parse import urlencode
from urllib.request import HTTPCookieProcessor, Request, build_opener

BASE = "https://www.koreabaseball.com"
URL = f"{BASE}/Record/Player/HitterBasic/Basic1.aspx"
PREFIX = "ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$"
F_SEASON = PREFIX + "ddlSeason$ddlSeason"
F_SERIES = PREFIX + "ddlSeries$ddlSeries"
F_TEAM = PREFIX + "ddlTeam$ddlTeam"
F_POS = PREFIX + "ddlPos$ddlPos"
F_SITU = PREFIX + "ddlSituation$ddlSituation"
F_DETAIL = PREFIX + "ddlSituationDetail$ddlSituationDetail"

cookiejar = http.cookiejar.CookieJar()
opener = build_opener(HTTPCookieProcessor(cookiejar))


def get(url):
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with opener.open(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def post(url, data):
    req = Request(
        url,
        data=urlencode(data).encode("utf-8"),
        headers={
            "User-Agent": "Mozilla/5.0",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": BASE,
            "Referer": url,
        },
    )
    with opener.open(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="replace")


def parse_hidden(h):
    return {
        n: html.unescape(v)
        for n, v in re.findall(r'<input[^>]*type="hidden"[^>]*name="([^"]+)"[^>]*value="([^"]*)"', h, re.I)
    }


def parse_opts(h, field):
    m = re.search(r'<select[^>]*name="%s"[^>]*>(.*?)</select>' % re.escape(field), h, re.I | re.S)
    if not m:
        return []
    out = []
    for v, t in re.findall(r'<option[^>]*value="([^"]*)"[^>]*>(.*?)</option>', m.group(1), re.I | re.S):
        txt = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html.unescape(t))).strip()
        out.append((v, txt))
    return out


def selected(options, text_contains):
    for v, t in options:
        if text_contains in t:
            return v
    return options[0][0] if options else ""


h0 = get(URL)
print("GET title error:", "에러 | KBO홈페이지" in h0)
hidden0 = parse_hidden(h0)
season = selected(parse_opts(h0, F_SEASON), "2025")
series = selected(parse_opts(h0, F_SERIES), "정규")
team = selected(parse_opts(h0, F_TEAM), "한화")
pos = parse_opts(h0, F_POS)[0][0]
situ = selected(parse_opts(h0, F_SITU), "상대팀별")
print("codes:", season, series, team, pos, situ)

# Step1: trigger situation change
form1 = {
    "__EVENTTARGET": F_SITU,
    "__EVENTARGUMENT": "",
    **hidden0,
    F_SEASON: season,
    F_SERIES: series,
    F_TEAM: team,
    F_POS: pos,
    F_SITU: situ,
    F_DETAIL: "",
}
h1 = post(URL, form1)
print("POST1 title error:", "에러 | KBO홈페이지" in h1)
print("POST1 detail opts:", parse_opts(h1, F_DETAIL)[:12])

hidden1 = parse_hidden(h1)
form2 = {
    "__EVENTTARGET": "",
    "__EVENTARGUMENT": "",
    **hidden1,
    F_SEASON: season,
    F_SERIES: series,
    F_TEAM: team,
    F_POS: pos,
    F_SITU: situ,
    F_DETAIL: "LT",
}
h2 = post(URL, form2)
print("POST2 title error:", "에러 | KBO홈페이지" in h2)
print("has 문현빈:", "문현빈" in h2)
print("has 기록이 없습니다:", "기록이 없습니다" in h2)
