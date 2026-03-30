const DATA_ROOT = "./2025_정규시즌_한화_롯데";
const MATCH_ROOT = `${DATA_ROOT}/상대전_정리`;

const hero = document.getElementById("hero");
const revealItems = Array.from(document.querySelectorAll(".reveal-item"));
const battleTrigger = document.getElementById("row-headtohead");
const hanwhaLogo = document.getElementById("hanwhaLogo");
const lotteLogo = document.getElementById("lotteLogo");

const nodes = {
  headLeft: document.getElementById("headtohead-left"),
  headRight: document.getElementById("headtohead-right"),
  hitLeft: document.getElementById("hitters-left"),
  hitRight: document.getElementById("hitters-right"),
  pitLeft: document.getElementById("pitchers-left"),
  pitRight: document.getElementById("pitchers-right"),
  strongLeft: document.getElementById("strong-left"),
  strongRight: document.getElementById("strong-right"),
};

const uiState = {
  tables: {},
};

const TABLE_COLUMNS = {
  hitter: [
    { key: "선수명", label: "선수명", type: "text", sortable: true },
    { key: "AVG", label: "타율", type: "number", sortable: true },
    { key: "AB", label: "타수", type: "number", sortable: true },
    { key: "H", label: "안타", type: "number", sortable: true },
    { key: "PA", label: "타석", type: "number", sortable: true },
    { key: "HR", label: "홈런", type: "number", sortable: true },
    { key: "RBI", label: "타점", type: "number", sortable: true },
    { key: "2B", label: "2루타", type: "number", sortable: true },
    { key: "3B", label: "3루타", type: "number", sortable: true },
    { key: "G", label: "경기", type: "number", sortable: true },
  ],
  pitcher: [
    { key: "선수명", label: "선수명", type: "text", sortable: true },
    { key: "ERA", label: "ERA", type: "number", sortable: true },
    { key: "IP", label: "이닝", type: "ip", sortable: true },
    { key: "SO", label: "탈삼진", type: "number", sortable: true },
    { key: "GS", label: "선발", type: "number", sortable: true },
    { key: "W", label: "승", type: "number", sortable: true },
    { key: "L", label: "패", type: "number", sortable: true },
    { key: "H", label: "피안타", type: "number", sortable: true },
    { key: "HR", label: "피홈런", type: "number", sortable: true },
    { key: "BB", label: "볼넷", type: "number", sortable: true },
    { key: "WHIP", label: "WHIP", type: "number", sortable: true },
  ],
};

init().catch((error) => {
  console.error(error);
  nodes.headLeft.innerHTML = cardError("데이터를 불러오지 못했습니다.");
  nodes.headRight.innerHTML = cardError("경로를 확인해주세요.");
});

function setupReveal() {
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in-view");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.2 }
  );

  revealItems.forEach((item) => observer.observe(item));
}

function setupBattleTransition() {
  let inBattleMode = false;
  let ticking = false;

  const updateBattleMode = () => {
    const triggerTop = battleTrigger.getBoundingClientRect().top;
    const enterLine = window.innerHeight * 0.62;
    const exitLine = window.innerHeight * 0.76;

    // Use hysteresis (different enter/exit lines) to prevent flicker near threshold.
    if (!inBattleMode && triggerTop <= enterLine) {
      document.body.classList.add("battle-mode");
      inBattleMode = true;
    } else if (inBattleMode && triggerTop >= exitLine) {
      document.body.classList.remove("battle-mode");
      inBattleMode = false;
    }

    ticking = false;
  };

  const onScrollOrResize = () => {
    if (ticking) {
      return;
    }
    ticking = true;
    requestAnimationFrame(updateBattleMode);
  };

  window.addEventListener("scroll", onScrollOrResize, { passive: true });
  window.addEventListener("resize", onScrollOrResize);
  updateBattleMode();
}

function setupLogoGather() {
  if (!hanwhaLogo || !lotteLogo || !hero) {
    return;
  }

  let ticking = false;

  const updateLogoTransform = () => {
    const rect = hero.getBoundingClientRect();
    const scrollable = Math.max(rect.height - window.innerHeight, 1);
    const progress = clamp(-rect.top / scrollable, 0, 1);

    const leftX = -50 + progress * 50;
    const rightX = 50 - progress * 50;
    const scale = 1 + progress * 0.08;

    hanwhaLogo.style.transform = `translate(${leftX}%, -50%) scale(${scale})`;
    lotteLogo.style.transform = `translate(${rightX}%, -50%) scale(${scale})`;

    ticking = false;
  };

  const onScrollOrResize = () => {
    if (ticking) {
      return;
    }
    ticking = true;
    requestAnimationFrame(updateLogoTransform);
  };

  window.addEventListener("scroll", onScrollOrResize, { passive: true });
  window.addEventListener("resize", onScrollOrResize);
  updateLogoTransform();
}

function setupTableEvents() {
  document.addEventListener("click", (event) => {
    const sortButton = event.target.closest(".sort-btn");
    if (sortButton) {
      const tableId = sortButton.dataset.table;
      const key = sortButton.dataset.key;
      if (tableId && key) {
        handleSort(tableId, key);
      }
      return;
    }

    const loadMoreButton = event.target.closest(".load-more-btn");
    if (loadMoreButton) {
      const tableId = loadMoreButton.dataset.table;
      if (tableId) {
        toggleExpand(tableId);
      }
    }
  });
}

async function init() {
  setupBattleTransition();
  setupLogoGather();
  setupReveal();
  setupTableEvents();

  const [
    hanwhaHitter,
    lotteHitter,
    hanwhaPitcher,
    lottePitcher,
    summary,
    hhVsLtHit,
    ltVsHhHit,
    hhVsLtPit,
    ltVsHhPit,
    hanwhaStrongDetail,
    lotteStrongDetail,
  ] = await Promise.all([
    fetchJson(`${DATA_ROOT}/2025_한화_타자.json`),
    fetchJson(`${DATA_ROOT}/2025_롯데_타자.json`),
    fetchJson(`${DATA_ROOT}/2025_한화_투수.json`),
    fetchJson(`${DATA_ROOT}/2025_롯데_투수.json`),
    fetchJson(`${MATCH_ROOT}/2025_한화_롯데_상대전_요약.json`),
    fetchCsv(`${MATCH_ROOT}/2025_한화_타자_vs_롯데.csv`),
    fetchCsv(`${MATCH_ROOT}/2025_롯데_타자_vs_한화.csv`),
    fetchCsv(`${MATCH_ROOT}/2025_한화_투수_vs_롯데.csv`),
    fetchCsv(`${MATCH_ROOT}/2025_롯데_투수_vs_한화.csv`),
    fetchCsv(`${MATCH_ROOT}/2025_한화_강자_세부.csv`),
    fetchCsv(`${MATCH_ROOT}/2025_롯데_강자_세부.csv`),
  ]);

  renderHeadToHead(summary);

  createTableState({
    id: "hanwha-hitters",
    rows: excludePitchersFromHitters(
      normalizeRows(hanwhaHitter.rows || []),
      normalizeRows(hanwhaPitcher.rows || [])
    ),
    columns: TABLE_COLUMNS.hitter,
    defaultSortKey: "AVG",
    defaultSortDir: "desc",
    mountNode: nodes.hitLeft,
    title: "한화 전체 타자 기록",
    badge: "TOP 5 기본 표시",
  });

  createTableState({
    id: "lotte-hitters",
    rows: excludePitchersFromHitters(
      normalizeRows(lotteHitter.rows || []),
      normalizeRows(lottePitcher.rows || [])
    ),
    columns: TABLE_COLUMNS.hitter,
    defaultSortKey: "AVG",
    defaultSortDir: "desc",
    mountNode: nodes.hitRight,
    title: "롯데 전체 타자 기록",
    badge: "TOP 5 기본 표시",
  });

  createTableState({
    id: "hanwha-pitchers",
    rows: normalizeRows(hanwhaPitcher.rows || []),
    columns: TABLE_COLUMNS.pitcher,
    defaultSortKey: "ERA",
    defaultSortDir: "asc",
    mountNode: nodes.pitLeft,
    title: "한화 전체 투수 기록",
    badge: "TOP 5 기본 표시",
  });

  createTableState({
    id: "lotte-pitchers",
    rows: normalizeRows(lottePitcher.rows || []),
    columns: TABLE_COLUMNS.pitcher,
    defaultSortKey: "ERA",
    defaultSortDir: "asc",
    mountNode: nodes.pitRight,
    title: "롯데 전체 투수 기록",
    badge: "TOP 5 기본 표시",
  });

  renderTableById("hanwha-hitters");
  renderTableById("lotte-hitters");
  renderTableById("hanwha-pitchers");
  renderTableById("lotte-pitchers");

  renderStrongSection(
    normalizeRows(hhVsLtHit),
    normalizeRows(ltVsHhHit),
    normalizeRows(hhVsLtPit),
    normalizeRows(ltVsHhPit),
    normalizeRows(hanwhaStrongDetail),
    normalizeRows(lotteStrongDetail)
  );
}

async function fetchJson(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`JSON fetch failed: ${path}`);
  }
  return response.json();
}

async function fetchCsv(path) {
  const response = await fetch(path);
  if (!response.ok) {
    throw new Error(`CSV fetch failed: ${path}`);
  }
  const text = await response.text();
  return parseCsv(text);
}

function parseCsv(text) {
  const lines = text
    .replace(/\r/g, "")
    .split("\n")
    .filter((line) => line.trim().length > 0);

  if (lines.length < 2) {
    return [];
  }

  const headers = splitCsvLine(lines[0]);
  return lines.slice(1).map((line) => {
    const cols = splitCsvLine(line);
    const row = {};
    headers.forEach((h, i) => {
      row[h] = cols[i] ?? "";
    });
    return row;
  });
}

function splitCsvLine(line) {
  const output = [];
  let current = "";
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      if (inQuotes && line[i + 1] === '"') {
        current += '"';
        i += 1;
      } else {
        inQuotes = !inQuotes;
      }
      continue;
    }

    if (ch === "," && !inQuotes) {
      output.push(current);
      current = "";
      continue;
    }
    current += ch;
  }

  output.push(current);
  return output;
}

function normalizeRows(rows) {
  return rows.map((row) => {
    const normalized = {};
    Object.keys(row).forEach((key) => {
      normalized[String(key).trim()] = row[key];
    });
    return normalized;
  });
}

function excludePitchersFromHitters(hitterRows, pitcherRows) {
  const pitcherNames = new Set(
    pitcherRows
      .map((row) => String(row["선수명"] || "").trim())
      .filter((name) => name.length > 0)
  );

  return hitterRows.filter((row) => {
    const name = String(row["선수명"] || "").trim();
    return !pitcherNames.has(name);
  });
}

function renderHeadToHead(summary) {
  const detail = summary?.team_head_to_head_detail;

  const required = [
    "games",
    "hanwha_wins",
    "lotte_wins",
    "draws",
    "hanwha_team_avg_vs_lotte",
    "hanwha_team_era_vs_lotte",
    "lotte_team_avg_vs_hanwha",
    "lotte_team_era_vs_hanwha",
  ];

  const missing = required.filter(
    (key) => !detail || detail[key] === undefined || detail[key] === null || detail[key] === ""
  );

  if (missing.length > 0) {
    console.warn(
      `[DATA MISSING] 상대전적 상세 수치가 부족합니다. 필요한 필드: ${missing.join(", ")}`
    );
  }

  if (missing.length === 0) {
    nodes.headLeft.innerHTML = `
      <span class="badge">상대전적 세부</span>
      <h3>한화 이글스 vs 롯데 자이언츠</h3>
      <div class="stat-grid">
        <div class="stat-item"><div class="label">맞대결</div><div class="value">16전 10승 6패</div></div>
        <div class="stat-item"><div class="label">상대 팀 타율</div><div class="value">${detail.hanwha_team_avg_vs_lotte}</div></div>
        <div class="stat-item"><div class="label">상대 평균자책점</div><div class="value">${detail.hanwha_team_era_vs_lotte}</div></div>
        <div class="stat-item"><div class="label">우세</div><div class="value">한화 기준</div></div>
      </div>
    `;

    nodes.headRight.innerHTML = `
      <span class="badge">상대전적 세부</span>
      <h3>롯데 자이언츠 vs 한화 이글스</h3>
      <div class="stat-grid">
        <div class="stat-item"><div class="label">맞대결</div><div class="value">16전 6승 10패</div></div>
        <div class="stat-item"><div class="label">상대 팀 타율</div><div class="value">${detail.lotte_team_avg_vs_hanwha}</div></div>
        <div class="stat-item"><div class="label">상대 평균자책점</div><div class="value">${detail.lotte_team_era_vs_hanwha}</div></div>
        <div class="stat-item"><div class="label">우세</div><div class="value">롯데 기준</div></div>
      </div>
    `;
    return;
  }

  const hanwhaText = "16전 10승 6패 (한화 이글스 기준)";
  const lotteText = "16전 6승 10패 (롯데 자이언츠 기준)";

  nodes.headLeft.innerHTML = `
    <span class="badge">상대전적 세부</span>
    <h3>한화 이글스 기준 맞대결</h3>
    <div class="fallback-strong">${hanwhaText}</div>
    <p class="muted">상세 수치 필드(상대팀 타율/상대 평균자책점)가 없어 기본 문구를 출력했습니다.</p>
  `;

  nodes.headRight.innerHTML = `
    <span class="badge">상대전적 세부</span>
    <h3>롯데 자이언츠 기준 맞대결</h3>
    <div class="fallback-strong">${lotteText}</div>
    <p class="muted">상세 수치 필드(상대팀 타율/상대 평균자책점)가 없어 기본 문구를 출력했습니다.</p>
  `;
}

function parseRecord(recordText) {
  if (!recordText || typeof recordText !== "string") {
    return null;
  }

  const parts = recordText.split("-").map((v) => Number.parseInt(v, 10));
  if (parts.length !== 3 || parts.some((n) => Number.isNaN(n))) {
    return null;
  }

  const [w, l, d] = parts;
  return {
    w,
    l,
    d,
    total: w + l + d,
  };
}

function createTableState(config) {
  uiState.tables[config.id] = {
    id: config.id,
    rows: config.rows,
    columns: config.columns,
    sortKey: config.defaultSortKey,
    sortDir: config.defaultSortDir,
    defaultSortKey: config.defaultSortKey,
    defaultSortDir: config.defaultSortDir,
    expanded: false,
    mountNode: config.mountNode,
    title: config.title,
    badge: config.badge,
  };
}

function renderTableById(tableId) {
  const tableState = uiState.tables[tableId];
  if (!tableState) {
    return;
  }

  const sorted = [...tableState.rows].sort((a, b) =>
    compareRows(a, b, tableState.sortKey, tableState.sortDir, tableState.columns)
  );
  const visible = tableState.expanded ? sorted : sorted.slice(0, 5);
  const hasMore = sorted.length > 5;

  const headerHtml = tableState.columns
    .map((col) => {
      if (!col.sortable) {
        return `<th>${escapeHtml(col.label)}</th>`;
      }
      const indicator =
        tableState.sortKey === col.key
          ? `<span class="sort-indicator">${tableState.sortDir === "asc" ? "▲" : "▼"}</span>`
          : "";
      return `<th><button class="sort-btn" data-table="${tableState.id}" data-key="${escapeHtml(
        col.key
      )}">${escapeHtml(col.label)}${indicator}</button></th>`;
    })
    .join("");

  const rowHtml = visible
    .map((row) => {
      const cells = tableState.columns
        .map((col) => `<td>${escapeHtml(displayValue(row[col.key]))}</td>`)
        .join("");
      return `<tr>${cells}</tr>`;
    })
    .join("");

  tableState.mountNode.innerHTML = `
    <span class="badge">${escapeHtml(tableState.badge)}</span>
    <h3>${escapeHtml(tableState.title)}</h3>
    <p class="section-sub">헤더를 클릭하면 정렬됩니다. 정렬 후에는 다시 TOP 5부터 표시됩니다.</p>
    <div class="table-scroll">
      <table class="record-table">
        <thead><tr>${headerHtml}</tr></thead>
        <tbody>${
          rowHtml || `<tr><td colspan="${tableState.columns.length}">데이터가 없습니다.</td></tr>`
        }</tbody>
      </table>
    </div>
    ${
      hasMore
        ? `<div class="table-actions"><button class="load-more-btn" data-table="${tableState.id}">${
            tableState.expanded ? "접기" : "더보기"
          }</button></div>`
        : ""
    }
  `;
}

function handleSort(tableId, key) {
  const tableState = uiState.tables[tableId];
  if (!tableState) {
    return;
  }

  if (tableState.sortKey === key) {
    tableState.sortDir = tableState.sortDir === "asc" ? "desc" : "asc";
  } else {
    tableState.sortKey = key;
    tableState.sortDir = defaultSortDirection(key);
  }

  tableState.expanded = false;
  renderTableById(tableId);
}

function toggleExpand(tableId) {
  const tableState = uiState.tables[tableId];
  if (!tableState) {
    return;
  }
  tableState.expanded = !tableState.expanded;
  renderTableById(tableId);
}

function defaultSortDirection(key) {
  if (key === "ERA") {
    return "asc";
  }
  if (key === "IP") {
    return "desc";
  }
  return "desc";
}

function compareRows(a, b, key, dir, columns) {
  const col = columns.find((entry) => entry.key === key);
  const type = col?.type || "text";

  let compare = 0;
  if (type === "number") {
    compare = compareNumber(toNum(a[key]), toNum(b[key]));
  } else if (type === "ip") {
    compare = compareNumber(ipToOuts(a[key]), ipToOuts(b[key]));
  } else {
    compare = String(displayValue(a[key])).localeCompare(String(displayValue(b[key])), "ko");
  }

  return dir === "asc" ? compare : -compare;
}

function compareNumber(a, b) {
  const na = a ?? Number.NEGATIVE_INFINITY;
  const nb = b ?? Number.NEGATIVE_INFINITY;
  if (na > nb) {
    return 1;
  }
  if (na < nb) {
    return -1;
  }
  return 0;
}

function renderStrongSection(
  hhVsLtHit,
  ltVsHhHit,
  hhVsLtPit,
  ltVsHhPit,
  hanwhaStrongDetail,
  lotteStrongDetail
) {
  const hhHitRequired = ["PA", "AVG", "H", "HR"];
  const ltHitRequired = ["PA", "AVG", "H", "HR"];
  const hhPitRequired = ["IP", "ERA", "SO", "GS"];
  const ltPitRequired = ["IP", "ERA", "SO", "GS"];

  const hhHitMissing = warnMissingFields("한화 타자 vs 롯데", hhVsLtHit, hhHitRequired);
  const ltHitMissing = warnMissingFields("롯데 타자 vs 한화", ltVsHhHit, ltHitRequired);
  const hhPitMissing = warnMissingFields("한화 투수 vs 롯데", hhVsLtPit, hhPitRequired);
  const ltPitMissing = warnMissingFields("롯데 투수 vs 한화", ltVsHhPit, ltPitRequired);

  const hhTop = topHittersByAvg(hhVsLtHit, 5);
  const ltTop = topHittersByAvg(ltVsHhHit, 5);
  const hhStarter = pickStarter(hhVsLtPit);
  const ltStarter = pickStarter(ltVsHhPit);

  const hhMerged = mergeStrongDetail(hhTop, hhStarter, hanwhaStrongDetail, "롯데");
  const ltMerged = mergeStrongDetail(ltTop, ltStarter, lotteStrongDetail, "한화");

  nodes.strongLeft.innerHTML = `
    <span class="badge">상대 팀 강자 기록</span>
    <h3>롯데 상대로 잘했던 한화</h3>
    ${renderStrongDetailTables(hhMerged)}
    ${
      hhHitMissing.length
        ? `<p class="field-warning">필드 부족: ${escapeHtml(hhHitMissing.join(", "))}</p>`
        : ""
    }
    ${
      hhPitMissing.length
        ? `<p class="field-warning">필드 부족: ${escapeHtml(hhPitMissing.join(", "))}</p>`
        : ""
    }
  `;

  nodes.strongRight.innerHTML = `
    <span class="badge">상대 팀 강자 기록</span>
    <h3>한화 상대로 잘했던 롯데</h3>
    ${renderStrongDetailTables(ltMerged)}
    ${
      ltHitMissing.length
        ? `<p class="field-warning">필드 부족: ${escapeHtml(ltHitMissing.join(", "))}</p>`
        : ""
    }
    ${
      ltPitMissing.length
        ? `<p class="field-warning">필드 부족: ${escapeHtml(ltPitMissing.join(", "))}</p>`
        : ""
    }
  `;
}

function renderStrongDetailTables(rows) {
  if (!rows.length) {
    return "<p class='muted'>상대 팀 강자 세부 CSV가 비어 있습니다.</p>";
  }

  const hitterRows = rows.filter((row) => String(row["구분"] || "").trim() === "타자");
  const pitcherRows = rows.filter((row) => String(row["구분"] || "").trim() === "투수");

  return `
    <p class="section-sub">타자 TOP 5 + 선발투수 1명 세부 기록</p>
    ${renderStrongTableBlock("타자 강자", hitterRows, ["선수명", "PA", "AVG", "H", "HR", "비고"])}
    ${renderStrongTableBlock("투수 강자", pitcherRows, ["선수명", "ERA", "IP", "SO", "GS", "비고"])}
  `;
}

function renderStrongTableBlock(title, rows, preferredColumns) {
  if (!rows.length) {
    return `<div class="strong-block"><h4>${escapeHtml(title)}</h4><p class="muted">해당 데이터가 없습니다.</p></div>`;
  }

  const columns = preferredColumns.filter((col) => {
    if (col === "선수명") {
      return true;
    }
    return rows.some((row) => row[col] !== undefined && row[col] !== null && String(row[col]).trim() !== "");
  });

  const header = columns.map((c) => `<th>${escapeHtml(c)}</th>`).join("");
  const body = rows
    .map(
      (row) => `<tr>${columns.map((c) => `<td>${escapeHtml(displayValue(row[c]))}</td>`).join("")}</tr>`
    )
    .join("");

  return `
    <div class="strong-block">
      <h4>${escapeHtml(title)}</h4>
      <div class="table-scroll">
        <table class="record-table">
          <thead><tr>${header}</tr></thead>
          <tbody>${body}</tbody>
        </table>
      </div>
    </div>
  `;
}

function mergeStrongDetail(topHitRows, starterRow, detailRows, opponentTeam) {
  if (detailRows && detailRows.length) {
    return detailRows;
  }

  console.warn(
    `[DATA MISSING] 2025_*_강자_세부.csv 파일이 비어 있어 기존 데이터에서 임시 렌더링합니다. 대상 상대팀: ${opponentTeam}`
  );

  const hitterRows = topHitRows.map((row) => ({
    구분: "타자",
    상대팀: opponentTeam,
    선수명: row["선수명"],
    PA: row.PA,
    AVG: row.AVG,
    H: row.H,
    HR: row.HR,
    ERA: "",
    IP: "",
    SO: "",
    GS: "",
    비고: "상대전 타율 TOP5",
  }));

  const pitcherRows = starterRow
    ? [
        {
          구분: "투수",
          상대팀: opponentTeam,
          선수명: starterRow["선수명"],
          PA: "",
          AVG: "",
          H: "",
          HR: "",
          ERA: starterRow.ERA,
          IP: starterRow.IP,
          SO: starterRow.SO,
          GS: starterRow.GS,
          비고: "선발투수 1명",
        },
      ]
    : [];

  return [...hitterRows, ...pitcherRows];
}

function topHittersByAvg(rows, count) {
  return [...rows]
    .filter((row) => toNum(row.AVG) !== null)
    .sort((a, b) => toNum(b.AVG) - toNum(a.AVG))
    .slice(0, count);
}

function pickStarter(rows) {
  const withEra = rows.filter((row) => toNum(row.ERA) !== null);
  const starters = withEra.filter((row) => toNum(row.GS) > 0);
  const pool = starters.length ? starters : withEra;
  if (!pool.length) {
    return null;
  }
  pool.sort((a, b) => toNum(a.ERA) - toNum(b.ERA));
  return pool[0];
}

function warnMissingFields(datasetName, rows, requiredFields) {
  if (!rows.length) {
    console.warn(`[DATA MISSING] ${datasetName}: 데이터 행이 없습니다.`);
    return requiredFields;
  }

  const row = rows[0];
  const missing = requiredFields.filter((field) => !(field in row));
  if (missing.length) {
    console.warn(`[DATA MISSING] ${datasetName}: 필요한 필드가 없습니다 -> ${missing.join(", ")}`);
  }
  return missing;
}

function toNum(value) {
  if (value === undefined || value === null) {
    return null;
  }
  const text = String(value).replaceAll(",", "").trim();
  if (text === "" || text === "-") {
    return null;
  }
  const parsed = Number.parseFloat(text);
  return Number.isNaN(parsed) ? null : parsed;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function ipToOuts(ipText) {
  if (!ipText) {
    return 0;
  }
  const clean = String(ipText).trim();
  const parts = clean.split(" ");
  const whole = Number.parseInt(parts[0], 10);
  if (Number.isNaN(whole)) {
    return 0;
  }
  let outs = whole * 3;
  if (parts[1] === "1/3") {
    outs += 1;
  } else if (parts[1] === "2/3") {
    outs += 2;
  }
  return outs;
}

function displayValue(value) {
  if (value === undefined || value === null || value === "") {
    return "-";
  }
  return value;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function cardError(msg) {
  return `<h3>오류</h3><p class='muted'>${escapeHtml(msg)}</p>`;
}
