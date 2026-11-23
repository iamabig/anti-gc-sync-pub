#!/usr/bin/env python3
"""agentkit (AGS-KIT) — anti-gc-sync-pub 계약 검수 키 (레포 안에서 실행)

명령:
  init                         worklog/ 양식 생성 (있는 파일은 건드리지 않음)
  new-id <코드|IMP|DEF>        중복 없는 Task ID(등록된 에이전트 코드) 또는 IMP·DEF 번호
  context [--n 5] [--work KEY] [--max-chars 12000]
                               컨텍스트 팩 출력 (새 세션은 이것만 읽는다)
  check [--json PATH] [--summary PATH] [--strict] [--since 50] [--hook --msg FILE] [--ahead-max 3]
                               계약 점검 C1~C30. --strict면 🔴가 있을 때 종료코드 1
  hash <파일>                  글로벌 룰 블록의 버전과 SHA-256 (C8). 블록이 없으면 파일 전체 SHA-256
  terms <TERMS.md>             이 키의 SSOT 상수와 TERMS.md 비교 (다르면 종료코드 1)
  collab <폴더> [--forbid 문자열]… [--strict]
                               에이전트 간 TURN·REPORT 문서 점검 R1~R8 (머리 표, 근거, 단정, 금지 문자열, 서명 위치, Append-Only, 턴 순서, 이름)
  doctor [--strict]            설치 상태 점검
  version

표준 라이브러리만 사용합니다 (node 불필요, 메모리 부담 최소).
"""
import sys, os, re, json, hashlib, subprocess, datetime, glob, argparse

KIT_VERSION = "1.2.1"
SPEC = "anti-gc-sync-pub v1.2.1"

# ---- SSOT 상수 (TERMS.md와 같아야 함. `agentkit.py terms TERMS.md`로 비교) ----
TERMS_COMPONENTS = ["AGS", "AGS-SPEC", "AGS-HQ-<코드>", "AGS-RS", "AGS-GR-<코드>", "AGS-KIT", "AGS-CI", "AGS-WL"]
AGENT_CODES = {"CL": "Claude", "AG": "Antigravity (Gemini)", "US": "사용자(소유자)"}
MODES = ["THINK", "CODE", "SENSITIVE", "MAINT", "DEPLOY", "REVIEW"]
EXCLUSIVE_MODES = ["SENSITIVE", "MAINT", "DEPLOY"]
IMPL_STATES = ["MOCK", "PARTIAL", "STATIC", "PLANNED", "REAL"]
DEF_STATES = ["open", "fixing", "fixed", "wontfix"]
# ---------------------------------------------------------------------------------

CODE = r"[A-Z]{2}"
RE_ID = re.compile(r"^T-\d{8}-\d{4}-(" + CODE + r")(-[b-z])?$")
RE_FILE = re.compile(r"^(T-\d{8}-\d{4}-" + CODE + r"(?:-[b-z])?)_[a-z0-9-]+(\.(plan|walkthrough))?\.md$")
RE_ID_ANY = re.compile(r"T-\d{8}-\d{4}-" + CODE + r"(?:-[b-z])?")
RE_WORK = re.compile(r"^[a-z0-9][a-z0-9-]{2,60}$")
RE_IMP = re.compile(r"IMP-\d{8}-\d{2}")
RE_DEF = re.compile(r"DEF-\d{8}-\d{2}")
RE_IMPL_TAG = re.compile(r"@impl\s+(IMP-\d{8}-\d{2})\s+(" + "|".join(IMPL_STATES) + r")\s*:\s*\S")
RE_START = re.compile(r"▶\s*시작\s*\[([A-Za-z]+)\]")
RE_END = re.compile(r"■\s*종료\s*\[([A-Za-z]+)\]")
RE_SHA = re.compile(r"배포\s*SHA\s*[=:]\s*`?([0-9a-f]{7,40})", re.I)
RE_CLAIM = re.compile(r"100\s*%|완벽|완전(히)?\s*해결|기술적으로\s*해결|모두\s*해결|전부\s*해결|ALL\s*CLEAR|문제\s*없음", re.I)
RE_EVIDENCE = re.compile(r"\d+\s*/\s*\d+|`[^`]+`|exit\s*=?\s*\d|\b[0-9a-f]{7,40}\b|[\w./\-]+\.(py|ts|tsx|js|md|json|log|yml)\b|https?://", re.I)
RE_INFRA = re.compile(r"(^|/)(wrangler[^/]*\.(toml|jsonc?)|Dockerfile[^/]*|docker-compose[^/]*\.ya?ml|compose\.ya?ml|fly\.toml|vercel\.json|netlify\.toml|serverless\.ya?ml|Procfile)$|^\.github/workflows/(?!agent-contract\.yml$)[^/]+\.ya?ml$")
RE_DEPLOY_CFG = re.compile(r"(^|/)wrangler[^/]*\.(toml|jsonc?)$")
RE_OPS = re.compile(r"운영\s*(미)?\s*확인\s*[:：]\s*(.*)")
LIST_FILES = ["worklog/INDEX.md", "worklog/BADCASES.md", "worklog/DEFECTS.md", "worklog/IMPLEMENTATION.md"]
FAIL_WORDS = re.compile(r"실패|오류|에러|FAIL|\berror\b|exception|traceback|timeout|타임아웃", re.I)
OPEN = ("🟡", "🔴")
IN_CI = bool(os.environ.get("GITHUB_ACTIONS") or os.environ.get("CI"))
IGNORED_DIRTY = ("worklog/.agentkit-report.json", "agentkit-report.json", "agentkit-summary.md", ".wt/")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# ---------------- 공통 ----------------
def repo_root():
    try:
        out = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, timeout=20)
        if out.returncode == 0 and out.stdout.strip():
            return os.path.normpath(out.stdout.strip())
    except Exception:
        pass
    return os.getcwd()


def git(root, *args):
    try:
        r = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=60)
        return r.stdout if r.returncode == 0 else ""
    except Exception:
        return ""


def git_ok(root, *args):
    try:
        return subprocess.run(["git", "-C", root, *args], capture_output=True, timeout=60).returncode == 0
    except Exception:
        return False


def read(p):
    try:
        with open(p, encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def now_local():
    return datetime.datetime.now()  # OS 로컬 시계


def parse_time(s):
    m = re.search(r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2})", s or "")
    if not m:
        return None
    try:
        return datetime.datetime.strptime(m.group(1) + " " + m.group(2), "%Y-%m-%d %H:%M")
    except ValueError:
        return None


def id_date(i):
    m = re.search(r"-(\d{8})-", i or "")
    try:
        return datetime.datetime.strptime(m.group(1), "%Y%m%d") if m else None
    except ValueError:
        return None


def _fm_lines(lines):
    fm = {}
    for line in lines:
        if ":" in line and not line.lstrip().startswith("#"):
            k, v = line.split(":", 1)
            v = re.split(r"\s+#", v, maxsplit=1)[0].strip().strip('"').strip("'")
            fm[k.strip()] = v
    return fm


def parse_task(path):
    text = read(path).replace("\r\n", "\n").lstrip("﻿")
    fm, body, fm_style = {}, text, "none"
    if text.startswith("---"):
        parts = text.split("\n---", 1)
        if len(parts) == 2:
            fm, body, fm_style = _fm_lines(parts[0].splitlines()[1:]), parts[1], "frontmatter"
    else:
        m = re.search(r"^```ya?ml\s*\n(.*?)\n```", "\n".join(text.split("\n")[:60]), re.S | re.M)
        if m and "id:" in m.group(1):
            fm, fm_style = _fm_lines(m.group(1).splitlines()), "fenced"
            body = text[:m.start()] + text[m.end():]
    sections, cur = {}, None
    for line in body.splitlines():
        m = re.match(r"^##\s*(\d+)\.", line)
        if m:
            cur = int(m.group(1))
            sections[cur] = []
            continue
        if cur is not None:
            sections[cur].append(line)
    sec = {k: "\n".join(v).strip() for k, v in sections.items()}
    status = (fm.get("status") or "")[:1]
    return {"path": path, "name": os.path.basename(path), "fm": fm, "sec": sec, "status": status, "fm_style": fm_style}


TEMPLATE_PHRASES = ["파일과 변경 요약", "실행한 명령", "출력 요약 (비밀값 제외)", "다음 에이전트(또는 다음 세션)가",
                    "필요한 결정과 누가 결정해야", "무엇을, 왜", "접근 방법. 바꿀 파일", "실행한 테스트와 통과 여부",
                    "(예: `npm run test:all` 94건 중 94 통과. 안 돌렸으면 이유)", "계획 대비 실제", "남은 MOCK·PARTIAL",
                    "(IMP 번호, 없으면 \"없음\". MOCK·PARTIAL을 배포했다면 \"화면 표시 확인\" 결과)", "배포 여부",
                    "(안 함 / 함 → 배포 SHA)", "사후 분석", "이것만 읽고 이어갈 수 있게.", "하는지."]


def meaningful(s):
    s = s or ""
    for p in TEMPLATE_PHRASES:
        s = s.replace(p, "")
    s = re.sub(r"[\-\*\|:#>\s]|남은 것|검증 못 한 것|바꾼 것|검증 방법|실제 결과|테스트 결과|막혔다면", "", s)
    return len(s) >= 10


def table_rows(text):
    rows = []
    for line in (text or "").splitlines():
        line = line.strip()
        if line.startswith("|") and not re.match(r"^\|[\s\-|:]+\|$", line):
            rows.append([c.strip() for c in line.strip("|").split("|")])
    return [r for r in rows[1:] if any(c for c in r)] if rows else []


def table_dicts(text, id_re):
    """머리줄 이름으로 읽는 표. 첫 칸이 id_re로 시작하는 줄만."""
    header, out = None, []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line.startswith("|") or re.match(r"^\|[\s\-|:]+\|$", line):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if cells and id_re.fullmatch(cells[0].strip("`[] ")):
            d = dict(zip(header, cells + [""] * len(header)))
            d["_id"] = cells[0].strip("`[] ")
            out.append(d)
    return out


def field(d, *names):
    for n in names:
        for k, v in d.items():
            if k.startswith(n):
                return v.strip()
    return ""


def has_incident(text):
    if table_rows(text):
        return True
    items = [l for l in (text or "").splitlines() if re.match(r"^\s*(\d+[.)]|[-*])\s+\S", l)]
    items = [l for l in items if not re.search(r"^\s*(\d+[.)]|[-*])\s*(없음|해당 없음|none)\s*$", l, re.I)]
    return len(items) >= 2


NEG_FAIL = re.compile(r"(실패|오류|에러|error|fail\w*|exception|timeout|타임아웃)\s*(은|는|이|가)?\s*(0\s*건|0\b|없음|없이|없었|발생하지)", re.I)


def has_failure(text):
    return bool(FAIL_WORDS.search(NEG_FAIL.sub("", text or "")))


def load(root):
    wl = os.path.join(root, "worklog")
    tasks = [parse_task(p) for p in sorted(glob.glob(os.path.join(wl, "tasks", "**", "*.md"), recursive=True))]
    return wl, tasks, read(os.path.join(wl, "NOW.md")), read(os.path.join(wl, "INDEX.md")), read(os.path.join(wl, "BADCASES.md"))


def task_id_of(t):
    m = RE_FILE.match(t["name"])
    return m.group(1) if m else (t["fm"].get("id") or t["name"])


def parse_locks(now):
    """NOW.md '작업 중 에이전트' 표. 머리줄 이름으로 읽음 (v1.2: 모드 열)."""
    sect, lines = False, []
    for line in now.splitlines():
        if "작업 중 에이전트" in line:
            sect = True; continue
        if sect and line.startswith("## "):
            break
        if sect and line.strip().startswith("|"):
            lines.append(line)
    header, locks = None, []
    for line in lines:
        if re.match(r"^\s*\|[\s\-|:]+\|\s*$", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if header is None:
            header = cells; continue
        if cells and re.fullmatch(CODE, cells[0] or ""):
            d = dict(zip(header, cells + [""] * len(header)))
            locks.append({"agent": cells[0], "task": field(d, "Task"), "mode": field(d, "모드").upper(),
                          "branch": field(d, "브랜치"), "area": field(d, "건드리는"), "started": field(d, "시작")})
    return locks, bool(header and any("모드" in h for h in header))


def load_lists(wl):
    impl_text, def_text = read(os.path.join(wl, "IMPLEMENTATION.md")), read(os.path.join(wl, "DEFECTS.md"))
    return table_dicts(impl_text, RE_IMP), table_dicts(def_text, RE_DEF), bool(impl_text), bool(def_text)


def open_items(wl):
    impls, defs, _, _ = load_lists(wl)
    oi = [{"id": d["_id"], "state": field(d, "상태"), "feature": field(d, "기능"), "location": field(d, "위치"),
           "display": field(d, "화면"), "until": field(d, "실제화 조건")} for d in impls if field(d, "상태") in ("MOCK", "PARTIAL", "PLANNED", "STATIC")]
    od = [{"id": d["_id"], "severity": field(d, "심각도"), "status": field(d, "상태"), "summary": field(d, "한 줄"),
           "fix_task": field(d, "수정")} for d in defs if field(d, "상태").lower() in ("open", "fixing")]
    return oi, od


def git_state(root):
    st = {"branch": git(root, "rev-parse", "--abbrev-ref", "HEAD").strip(), "upstream": "", "ahead": None, "behind": None,
          "unpushed": None, "dirty": [], "worktree": False}
    if git(root, "remote").strip():
        n = git(root, "rev-list", "--count", "HEAD", "--not", "--remotes").strip()
        st["unpushed"] = int(n) if n.isdigit() else None  # 원격 어느 브랜치에도 없는 커밋 (새 브랜치에 섞여 온 것 포함)
    up = git(root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").strip()
    if up:
        st["upstream"] = up
        lr = git(root, "rev-list", "--left-right", "--count", f"{up}...HEAD").split()
        if len(lr) == 2:
            st["behind"], st["ahead"] = int(lr[0]), int(lr[1])
    for line in git(root, "status", "--porcelain", "--untracked-files=all").splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip().strip('"')
        if any(path.startswith(x) or path == x for x in IGNORED_DIRTY) or "__pycache__/" in path or path.endswith(".pyc"):
            continue
        st["dirty"].append({"x": line[0], "y": line[1], "path": path})
    gd = os.path.normcase(os.path.abspath(os.path.join(root, git(root, "rev-parse", "--git-dir").strip() or ".git")))
    gc = os.path.normcase(os.path.abspath(os.path.join(root, git(root, "rev-parse", "--git-common-dir").strip() or ".git")))
    st["worktree"] = gd != gc
    return st


def owned(path, locks):
    """미커밋 파일이 어떤 잠금 줄의 '건드리는 영역'에 들어가는가 (C22).
    영역 칸에 경로(앞부분)·파일 이름·폴더 이름을 적으면 그 아래가 주인 있음. '전체'·'*'는 전부. worklog/는 잠금이 하나라도 있으면 주인 있음."""
    p = path.replace("\\", "/").strip("/")
    if p.startswith("worklog/") and locks:
        return True
    for l in locks:
        area = l["area"].replace("\\", "/")
        if re.search(r"전체|\*|\ball\b", area):
            return True
        for tok in re.split(r"[\s,·;]+|`", area):
            tok = tok.strip().strip("/")
            if len(tok) >= 2 and (p == tok or p.startswith(tok + "/") or os.path.basename(p) == tok or tok in p.split("/")[:-1]):
                return True
    return False


def agent_of(tid):
    m = re.match(r"T-\d{8}-\d{4}-([A-Z]{2})", tid or "")
    return m.group(1) if m else None


def default_branch(root):
    ref = git(root, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD").strip()
    if ref:
        return ref.rsplit("/", 1)[-1]
    for b in ("main", "master"):
        if git_ok(root, "rev-parse", "--verify", "--quiet", b):
            return b
    return None


def unsupported_claims(text):
    """근거 없는 단정(C28): 같은 줄에 숫자·명령·파일·실측 표시가 없는 '100%·완벽·해결됨' 류."""
    out = []
    for line in (text or "").splitlines():
        bare = re.sub(r"\"[^\"]*\"|“[^”]*”|'[^']*'", "", line)  # 남의 말을 따옴표로 인용한 것은 제외
        if RE_CLAIM.search(bare) and not RE_EVIDENCE.search(RE_CLAIM.sub("", line)):
            out.append(line.strip()[:100])
    return out


def unsupported_measure(text):
    """'실측'이라고 썼는데 같은 줄에 명령·출력·해시·파일 근거가 없는 줄 (C30)."""
    out = []
    for line in (text or "").splitlines():
        bare = re.sub(r"\"[^\"]*\"|“[^”]*”|'[^']*'", "", line)
        if "실측" in bare and not RE_EVIDENCE.search(bare.replace("실측", "")):
            out.append(line.strip()[:100])
    return out


def _strings(block):
    return sorted(set(re.findall(r'"([^"\n]+)"', block or "")))


def deploy_configs(root):
    """배포 설정(wrangler)의 이름·cron·route (C29). 첫 'name'을 워커 이름으로 본다."""
    out = []
    for f in git(root, "ls-files").splitlines():
        if not RE_DEPLOY_CFG.search(f) or "node_modules/" in f:
            continue
        t = read(os.path.join(root, f))
        t = re.sub(r"(?m)^\s*(//|#).*$", "", t)
        t = re.sub(r'(?m)(^[^"\n]*("[^"\n]*"[^"\n]*)*?)\s+//.*$', r"\1", t)
        m = re.search(r'"name"\s*:\s*"([^"]+)"', t) or re.search(r'(?m)^name\s*=\s*"([^"]+)"', t)
        if not m:
            continue
        cr = re.search(r'"?crons"?\s*[:=]\s*\[(.*?)\]', t, re.S)
        routes = re.findall(r'"?pattern"?\s*[:=]\s*"([^"]+)"', t) + re.findall(r'(?m)^route\s*=\s*"([^"]+)"', t)
        out.append({"file": f, "name": m.group(1), "crons": _strings(cr.group(1)) if cr else [], "routes": sorted(set(routes))})
    return out


def removed_rows(diff_text, current):
    """diff에서 지워진 목록 줄(ID 있는 표 줄) 중, 같은 diff에서 다시 추가되지 않았고 지금 파일에도 없는 것 (C27)."""
    rx = re.compile(RE_ID_ANY.pattern + "|" + RE_IMP.pattern + "|" + RE_DEF.pattern)
    gone, added = {}, set()
    for line in diff_text.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added |= set(rx.findall(line))
        elif line.startswith("-") and not line.startswith("---") and line[1:].lstrip().startswith("|"):
            ids = rx.findall(line)
            if ids:
                gone[ids[0]] = line[1:].strip()[:90]
    return {i: l for i, l in gone.items() if i not in added and i not in current}


def v12_adopt_time(root):
    """v1.2 도입 시각 = worklog/IMPLEMENTATION.md 또는 DEFECTS.md가 처음 커밋된 때. 없으면 None."""
    ts = git(root, "log", "--format=%ct", "--diff-filter=A", "--", "worklog/IMPLEMENTATION.md", "worklog/DEFECTS.md").split()
    return datetime.datetime.fromtimestamp(int(ts[-1])) if ts else None


# ---------------- init / new-id / hash / terms ----------------
TPL_NOW = """# NOW — {repo} 현재 상태

> 갱신: {now} KST · 갱신자: {who}
> **모든 에이전트는 작업 전에 컨텍스트 팩을 읽습니다** (`python .agentkit/agentkit.py context`).

## 🔒 작업 중 에이전트 (동시 작업 잠금, CONTRACT §12)
| 에이전트 | Task ID | 모드 | 브랜치 | 건드리는 파일/영역 | 시작 (KST) |
|---|---|---|---|---|---|

> 모드: THINK · CODE · SENSITIVE · MAINT · DEPLOY · REVIEW. SENSITIVE·MAINT·DEPLOY는 단독 (다른 줄이 있으면 기다림).

## 🟡 진행 중
- (없음)

## 🔴 막힘 (결정 필요)
- (없음)

## ⏭️ 다음 할 일
1.

## ✅ 최근 완료 (3건)
-

## ⚠️ 이 레포에서 꼭 알아야 할 것
-
"""
TPL_INDEX = """# INDEX — {repo} 작업 타임라인

> 최신이 위. 작업 1건 = 1줄. 상태: 🟡진행 🟢완료 🔴막힘 ⚪보류 ❌취소 · 평가: pass / partial / bad-case

| 상태 | Task ID | 시작 (KST) | 에이전트 | 우선순위 | 작업 키 | 제목 | 평가 |
|---|---|---|---|---|---|---|---|
"""
TPL_BAD = """# BADCASES — {repo} 배드 케이스 타임라인

> 최신이 위. 1건 1줄. 상세는 해당 Task 파일 §8. 배드 케이스는 벌이 아니라 다음 작업을 위한 교훈입니다.

| 일시 (KST) | Task ID | 에이전트 | 유형 | 한 줄 교훈 |
|---|---|---|---|---|
"""
TPL_IMPL = """# IMPLEMENTATION — {repo} 구현 상태 목록 (CONTRACT §16)

> 하드코딩·목업·미구현을 한 곳에서 관리합니다. 1항목 = 1번호. Task는 번호로만 참조합니다.
> 코드에는 그 자리에 한 줄: `// @impl IMP-YYYYMMDD-NN MOCK: 한 줄 설명` (번호는 `agentkit.py new-id IMP`)
> 상태: MOCK · PARTIAL · STATIC · PLANNED · REAL. REAL이 되면 코드 표시를 지우고 이 줄은 남깁니다.

| 번호 | 상태 | 기능 | 위치 (파일:줄) | 화면 표시 | 실제화 조건 | 만든 Task | 실제화 Task |
|---|---|---|---|---|---|---|---|
"""
TPL_DEF = """# DEFECTS — {repo} 결함 목록 (CONTRACT §17)

> 제품의 결함(버그)을 관리합니다. 1결함 = 1번호 (`agentkit.py new-id DEF`). 에이전트 작업 방식의 문제는 BADCASES.md.
> 심각도: P0 · P1 · P2 · P3 / 상태: open · fixing · fixed · wontfix. 최신이 위.

| 번호 | 심각도 | 상태 | 한 줄 설명 | 발견 Task | 수정 Task |
|---|---|---|---|---|---|
"""


def cmd_init(args):
    root = repo_root()
    wl = os.path.join(root, "worklog")
    os.makedirs(os.path.join(wl, "tasks"), exist_ok=True)
    repo = os.path.basename(root)
    made = []
    for name, tpl in (("NOW.md", TPL_NOW), ("INDEX.md", TPL_INDEX), ("BADCASES.md", TPL_BAD),
                      ("IMPLEMENTATION.md", TPL_IMPL), ("DEFECTS.md", TPL_DEF)):
        p = os.path.join(wl, name)
        if not os.path.exists(p):
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                f.write(tpl.format(repo=repo, now=now_local().strftime("%Y-%m-%d %H:%M"), who=args.who))
            made.append(name)
    print("만든 파일:", ", ".join(made) if made else "없음 (이미 있음)")
    print("작업 파일 양식은 원본 저장소 templates/TASK.md 를 따릅니다.")


def scan_impl_tags(root):
    out = git(root, "grep", "-n", "-I", "--untracked", "-e", "@impl", "--", ".",
              ":(exclude)*.md", ":(exclude).agentkit/*", ":(exclude)worklog/*")
    tags = []
    for line in out.splitlines():
        m = re.match(r"^(.*?):(\d+):(.*)$", line)
        if not m:
            continue
        f, n, txt = m.groups()
        if "@impl" not in txt:
            continue
        t = RE_IMPL_TAG.search(txt)
        tags.append({"file": f, "line": int(n), "id": t.group(1) if t else None, "state": t.group(2) if t else None,
                     "raw": txt.strip()[:120]})
    return tags


def cmd_new_id(args):
    root = repo_root()
    wl, tasks, _, index, _ = load(root)
    kind = args.agent
    if kind in ("IMP", "DEF"):
        lst = read(os.path.join(wl, "IMPLEMENTATION.md" if kind == "IMP" else "DEFECTS.md"))
        pool = lst + "\n" + "\n".join(read(t["path"]) for t in tasks)
        if kind == "IMP":
            pool += "\n" + "\n".join(t["raw"] for t in scan_impl_tags(root))
        used = set(re.findall(kind + r"-\d{8}-\d{2}", pool))
        day = now_local().strftime("%Y%m%d")
        n = 1
        while f"{kind}-{day}-{n:02d}" in used:
            n += 1
        print(f"{kind}-{day}-{n:02d}")
        return
    if kind not in AGENT_CODES:
        print(f"등록되지 않은 에이전트 코드: {kind}. TERMS.md §2에 등록하고 새 AGS-KIT를 받으세요. 등록: {', '.join(AGENT_CODES)}")
        sys.exit(2)
    used = {task_id_of(t) for t in tasks} | set(RE_ID_ANY.findall(index))
    base = "T-" + now_local().strftime("%Y%m%d-%H%M") + "-" + kind
    cand = base
    for suf in [""] + ["-" + c for c in "bcdefghijklmnopqrstuvwxyz"]:
        cand = base + suf
        if cand not in used:
            break
    month = now_local().strftime("%Y-%m")
    print(cand)
    if args.slug:
        print(f"worklog/tasks/{month}/{cand}_{args.slug}.md")


def cmd_hash(args):
    raw = read(args.file)
    text = raw.replace("\r\n", "\n")
    m = re.search(r"(<!-- anti-gc-sync-pub (v[\d.]+[^ ]*).*?<!-- /anti-gc-sync-pub [^>]*-->)", text, re.S)
    if not m:
        with open(args.file, "rb") as f:
            print(f"sha256(file): {hashlib.sha256(f.read()).hexdigest()}")
        return
    block, ver = m.group(1), m.group(2)
    print(f"version: {ver}")
    print(f"sha256: {hashlib.sha256(block.encode('utf-8')).hexdigest()}")
    print(f"first_line: {block.splitlines()[0]}")


def terms_from_md(text):
    sec, got = None, {"components": [], "codes": [], "modes": [], "impl": [], "def": []}
    for line in text.replace("\r\n", "\n").splitlines():
        h = re.match(r"^##\s*(\d+)\.", line)
        if h:
            sec = int(h.group(1)); continue
        if not line.startswith("|") or re.match(r"^\|[\s\-|:]+\|$", line):
            continue
        first = line.strip("|").split("|")[0].strip()
        m = re.fullmatch(r"`([^`]+)`", first)
        if not m:
            continue
        v = m.group(1)
        key = {1: "components", 2: "codes", 4: "modes", 5: "impl", 6: "def"}.get(sec)
        if key:
            got[key].append(v)
    return got


def cmd_terms(args):
    got = terms_from_md(read(args.file))
    want = {"components": TERMS_COMPONENTS, "codes": list(AGENT_CODES), "modes": MODES, "impl": IMPL_STATES, "def": DEF_STATES}
    bad = 0
    for k, v in want.items():
        same = sorted(v) == sorted(got[k])
        bad += 0 if same else 1
        print(("🟢 " if same else "🔴 ") + f"{k}: 키={v}" + ("" if same else f" / TERMS={got[k]}"))
    print("결과:", "일치" if not bad else f"불일치 {bad}건 → TERMS.md와 AGS-KIT 상수를 맞추세요")
    if bad:
        sys.exit(1)


# ---------------- collab (HQ 간 턴·보고서 파이프라인) ----------------
RE_TURN_NAME = re.compile(r"^TURN-(\d{3})-(\d{2})_(" + CODE + r")_[a-z0-9-]+\.md$")
RE_REPORT_NAME = re.compile(r"^REPORT-(\d{8}-\d{4})-(" + CODE + r")_[a-z0-9-]+\.md$")


def head_table(text):
    rows = [l for l in text.splitlines()[:15] if l.strip().startswith("|") and not re.match(r"^\s*\|[\s\-|:]+\|\s*$", l)]
    if len(rows) < 2:
        return {}
    h = [c.strip().replace("*", "") for c in rows[0].strip().strip("|").split("|")]
    v = [c.strip().replace("*", "") for c in rows[1].strip().strip("|").split("|")]
    return dict(zip(h, v))


def cmd_collab(args):
    d = args.dir
    files = sorted(f for f in os.listdir(d) if f.endswith(".md") and not f.startswith("_"))
    res = []
    ledger_p = os.path.join(d, ".collab-ledger.json")
    try:
        ledger = json.load(open(ledger_p, encoding="utf-8"))
    except Exception:
        ledger = {}
    new_ledger, turns = {}, {}
    for f in files:
        text = read(os.path.join(d, f)).replace("\r\n", "\n")
        mt, mr = RE_TURN_NAME.match(f), RE_REPORT_NAME.match(f)
        kind = "TURN" if mt else ("REPORT" if mr else ("LEGACY" if re.match(r"^(REQUEST|RESPONSE)-", f) else "OTHER"))
        if kind == "OTHER":
            res.append(r("R8", "warn", f"{f}: 이름 규격 밖 (TURN-NNN-NN_XX_slug.md / REPORT-YYYYMMDD-HHmm-XX_slug.md)"))
        head = head_table(text)
        writer = head.get("쓴쪽", "")
        if kind in ("TURN", "REPORT"):
            code = (mt or mr).group(3 if mt else 2)
            if code not in AGENT_CODES:
                res.append(r("R8", "fail", f"{f}: 등록되지 않은 에이전트 코드 {code}"))
            if writer and code not in writer:
                res.append(r("R8", "warn", f"{f}: 파일 이름 코드 {code} ≠ 머리 표 쓴쪽 '{writer}'"))
            need = ["쓴쪽", "일시"] + (["다음 턴"] if kind == "TURN" else ["등급"])
            miss = [k for k in need if not any(k in h for h in head)]
            if miss:
                res.append(r("R1", "fail" if kind == "REPORT" else "warn", f"{f}: 머리 표에 {', '.join(miss)} 없음"))
            gm = re.search(r"^##\s*[\d.]*\s*근거.*?$(.*?)(?=^## |\Z)", text, re.M | re.S)
            if not gm or not re.search(r"실측|문서|추측", gm.group(1)):
                res.append(r("R2", "fail" if kind == "REPORT" else "warn", f"{f}: '근거' 절이 없거나 실측·문서·추측 표시가 없음"))
            for line in unsupported_claims(text):
                res.append(r("R3", "warn", f"{f}: 근거 없는 단정 → {line}"))
            if kind == "REPORT" and re.search(r"☑\s*서명|서명\s*(완료|함)", text):
                res.append(r("R5", "fail", f"{f}: 보고서에 서명 표기 → 서명은 TURN 문서의 서명 표에서만"))
            if mt:
                turns.setdefault(mt.group(1), []).append((mt.group(2), code, head.get("다음 턴", "") or next((v for k, v in head.items() if "다음 턴" in k), ""), f))
        for pat in args.forbid or []:
            if re.search(re.escape(pat), text, re.I):
                res.append(r("R4", "fail", f"{f}: 공유 문서에 쓰면 안 되는 문자열 '{pat}'"))
        lines = [hashlib.sha1(l.strip().encode("utf-8")).hexdigest()[:12] for l in text.splitlines() if l.strip()]
        new_ledger[f] = lines
        if f in ledger:
            gone = len(set(ledger[f]) - set(lines))
            if gone:
                res.append(r("R6", "fail", f"{f}: 지난 점검 이후 지워지거나 바뀐 줄 {gone}개 (Append-Only: 고칠 때는 덧붙이고 '정정'으로 표시)"))
    for f in ledger:
        if f not in new_ledger:
            res.append(r("R6", "fail", f"{f}: 지난 점검 이후 파일이 사라짐"))
    for topic, lst in turns.items():
        lst.sort()
        for (n1, c1, nxt, f1), (n2, c2, _, f2) in zip(lst, lst[1:]):
            if nxt and c2 not in nxt and "사용자" not in nxt:
                res.append(r("R7", "warn", f"TURN-{topic}: {f1}의 다음 턴 '{nxt}'인데 {f2}는 {c2}가 씀"))
    icon = {"pass": "🟢", "warn": "🟡", "fail": "🔴", "skip": "⚪", "info": "🔵"}
    print(f"agentkit {KIT_VERSION} collab · {os.path.basename(os.path.abspath(d))} · 문서 {len(files)}개")
    for x in res:
        print(f"{icon[x['level']]} {x['id']:<3} {x['msg']}")
    fails = sum(1 for x in res if x["level"] == "fail")
    print(f"요약: 🔴{fails} 🟡{sum(1 for x in res if x['level'] == 'warn')}" + (" · 문제 없음" if not res else ""))
    if not args.no_ledger:
        with open(ledger_p, "w", encoding="utf-8") as fp:
            json.dump(new_ledger, fp, ensure_ascii=False)
        print(f"장부 갱신: {os.path.basename(ledger_p)} (다음 점검에서 지워진 줄을 찾는 기준)")
    if args.strict and fails:
        sys.exit(1)


# ---------------- context ----------------
def summarize_task(t, keep=(1, 3, 6, 8)):
    fm = t["fm"]
    head = (f"### {task_id_of(t)} · {fm.get('title','')}  [{fm.get('status','')} {fm.get('priority','')} "
            f"mode={fm.get('mode','')} work={fm.get('work','')} plan={fm.get('plan','')} eval={fm.get('eval','')}]")
    parts = [head, f"(파일: {os.path.relpath(t['path'])})"]
    names = {1: "목표", 6: "인수인계", 8: "평가"}
    for k in keep:
        s = t["sec"].get(k)
        if not s:
            continue
        if k == 3:
            done = len(re.findall(r"^\s*-\s*\[[xX]\]|☑", s, re.M))
            todo = re.findall(r"^\s*-\s*\[\s\]\s*(.+)$", s, re.M)
            parts.append(f"- 체크리스트: 완료 {done} · 남음 {len(todo)}" + (" → " + " / ".join(x.strip() for x in todo[:5]) if todo else ""))
        else:
            parts.append(f"- {names[k]}: " + " ".join(s.split())[:600])
    return "\n".join(parts)


def git_block(root, now):
    st = git_state(root)
    locks, _ = parse_locks(now)
    ab = f"원격 {st['upstream']} 대비 앞섬 {st['ahead']} · 뒤처짐 {st['behind']}" if st["upstream"] else "원격 추적 브랜치 없음"
    out = ["## git 상태 (먼저 확인)", f"- 브랜치: `{st['branch']}`" + (" (git worktree)" if st["worktree"] else "") + f" · {ab}",
           f"- 원격 어디에도 없는 커밋: {st['unpushed']}",
           f"- 미커밋 파일: {len(st['dirty'])}" + (" → " + ", ".join(d["path"] for d in st["dirty"][:8]) if st["dirty"] else "")]
    if locks:
        out.append("- 잠금: " + " / ".join(f"{l['agent']} {l['task']} [{l['mode'] or '모드?'}] {l['branch']}" for l in locks))
    warn = []
    orphan = [d["path"] for d in st["dirty"] if not owned(d["path"], locks)]
    if orphan:
        warn.append(f"주인 없는 미커밋 변경 {len(orphan)}개 ({', '.join(orphan[:5])}) → 누구 것인지 확인 전에 그 파일·브랜치를 건드리지 않음 (C22)")
    for l in locks:
        b = l["branch"]
        if b and ".wt" not in b and b not in ("-", "—") and not st["worktree"] and b != st["branch"]:
            warn.append(f"{l['agent']} 잠금 브랜치 `{b}` ≠ 현재 `{st['branch']}` → 같은 폴더 브랜치 전환 금지 (C24)")
        if l["mode"] in EXCLUSIVE_MODES:
            warn.append(f"{l['agent']}가 {l['mode']} 모드(단독) 중 → 끝날 때까지 기다림 (C21)")
    if st["unpushed"]:
        warn.append(f"원격 어디에도 없는 커밋 {st['unpushed']}개 → 배포·PR 전에 주인과 push 여부 확인. 새 브랜치를 만들면 이 커밋들이 PR에 섞임 (C25)")
    out += [f"- ⚠️ {w}" for w in warn]
    return out


def cmd_context(args):
    root = repo_root()
    wl, tasks, now, index, bad = load(root)
    if not os.path.isdir(wl):
        print("worklog/ 가 없습니다. 먼저 `agentkit.py init` 을 실행하세요."); return
    out = [f"# 컨텍스트 팩 ({SPEC}, agentkit {KIT_VERSION}) — {os.path.basename(root)}",
           "> 이 출력만 읽고 시작합니다. 과거 Task가 더 필요하면 INDEX에서 찾아 그 파일 하나만 여세요.", ""]
    out += git_block(root, now) + [""]
    out += ["## NOW.md", now.strip(), ""]
    oi, od = open_items(wl)
    out += ["## 열린 결함 (DEFECTS.md open·fixing)"] + ([f"- {d['id']} {d['severity']} {d['status']} · {d['summary']}" + (f" · 수정 {d['fix_task']}" if d['fix_task'] else "") for d in od] or ["- (없음)"]) + [""]
    out += ["## 남은 구현 (IMPLEMENTATION.md MOCK·PARTIAL·STATIC·PLANNED) — 실제화하면 implements: 로 이어서"] + \
           ([f"- {i['id']} {i['state']} · {i['feature']} · {i['location']} · 화면 표시: {i['display'] or '없음!'} · 실제화 조건: {i['until']}" for i in oi] or ["- (없음)"]) + [""]
    focus = [t for t in tasks if t["status"] in OPEN or (args.work and t["fm"].get("work") == args.work)]
    out += ["## 진행 중·막힘·이번 작업 키 Task (요약)"] + ([summarize_task(t) for t in focus] or ["- (없음)"]) + [""]
    brows = [l for l in bad.splitlines() if l.startswith("|")]
    out += ["## BADCASES.md (최근 5건 = 교훈)"] + (brows[:7] if brows else ["- (없음)"]) + [""]
    rows = [l for l in index.splitlines() if l.startswith("|")]
    out += ["## INDEX.md (최근 %d건)" % args.n] + rows[:2 + args.n]
    text = "\n".join(out)
    if len(text) > args.max_chars:
        text = text[:args.max_chars] + f"\n\n…(잘림: {args.max_chars}자 제한. 필요한 파일만 따로 여세요)"
    print(text)


# ---------------- check ----------------
def r(cid, level, msg, items=None):
    return {"id": cid, "level": level, "msg": msg, "items": items or []}


def marks(t):
    log = t["sec"].get(4, "")
    return [m.upper() for m in RE_START.findall(log)], [(m.group(1).upper(), log[m.start():].split("\n", 1)[0]) for m in RE_END.finditer(log)]


def is_deploy(t):
    st, en = marks(t)
    return t["fm"].get("deploy", "").lower() == "yes" or t["fm"].get("mode", "").upper() == "DEPLOY" or "DEPLOY" in st


def cmd_check(args):
    root = repo_root()
    wl, tasks, now, index, bad = load(root)
    res = []
    if not os.path.isdir(wl):
        res.append(r("C0", "fail", "worklog/ 없음 (agentkit.py init 필요)"))
        return finish(args, root, res, [], [], [], [], {})
    ids = [task_id_of(t) for t in tasks]
    idset = set(ids)
    gst = git_state(root)
    dirty_paths = {d["path"].replace("\\", "/") for d in gst["dirty"]}

    adopt = git(root, "log", "--format=%ct", "--diff-filter=A", "--", "worklog/INDEX.md").split()
    adopt_ts = int(adopt[-1]) if adopt else None
    log = git(root, "log", "--no-merges", f"-n{args.since}", "--format=%x1e%H%x1f%s%x1f%ct", "--name-only")
    commits = []
    for chunk in log.split("\x1e")[1:]:
        lines = chunk.strip("\n").split("\n")
        h, s, ct = lines[0].split("\x1f")
        files = [f for f in lines[1:] if f.strip()]
        if adopt_ts is None or int(ct) >= adopt_ts:
            commits.append({"hash": h[:7], "subject": s, "ts": int(ct), "files": files})

    # C1
    if adopt_ts is None:
        commits = []
        res.append(r("C1", "skip", "worklog/INDEX.md가 아직 커밋되지 않음 → 도입 이후 커밋 없음 (첫 작업 커밋 뒤부터 점검)"))
    else:
        bad_c = [f"{c['hash']} {c['subject'][:60]}" for c in commits if not re.match(r"^\[" + RE_ID_ANY.pattern + r"\] ", c["subject"])]
        res.append(r("C1", "warn" if bad_c else "pass", f"TaskID 없는 커밋 {len(bad_c)}건 (worklog 도입 이후)", bad_c))
    if args.msg and not re.match(r"^\[(" + RE_ID_ANY.pattern + r")\] ", read(args.msg).lstrip("﻿")) and not read(args.msg).startswith(("Merge", "Revert")):
        res.append(r("C1", "warn", "지금 커밋 메시지 첫 줄에 [TaskID] 없음"))
    # C2
    idx_ids = set(RE_ID_ANY.findall(index))
    miss_idx = sorted(idset - idx_ids); miss_file = sorted(idx_ids - idset)
    res.append(r("C2", "warn" if (miss_idx or miss_file) else "pass",
                 f"INDEX에 없는 Task {len(miss_idx)} · 파일 없는 INDEX 줄 {len(miss_file)}",
                 [f"INDEX 누락: {i}" for i in miss_idx] + [f"파일 누락: {i}" for i in miss_file]))
    # C3
    stale = []
    for t in tasks:
        if t["status"] == "🟡":
            u = parse_time(t["fm"].get("updated"))
            if u and (now_local() - u).total_seconds() > 72 * 3600:
                stale.append(f"{task_id_of(t)} (updated {t['fm'].get('updated')})")
    res.append(r("C3", "warn" if stale else "pass", f"72시간 넘게 갱신 없는 🟡 {len(stale)}건", stale))
    # C4
    now_ts = git(root, "log", "-1", "--format=%ct", "--", "worklog/NOW.md").strip()
    code_c = [c for c in commits if any(not f.startswith("worklog/") for f in c["files"])]
    if code_c and now_ts and code_c[0]["ts"] > int(now_ts):
        res.append(r("C4", "warn", "NOW.md가 마지막 작업 커밋보다 오래됨", [code_c[0]["hash"]]))
    else:
        res.append(r("C4", "pass", "NOW.md 최신"))
    # C5
    empty = [task_id_of(t) for t in tasks if t["status"] == "🟢" and not (meaningful(t["sec"].get(5)) and meaningful(t["sec"].get(6)))]
    res.append(r("C5", "fail" if empty else "pass", f"🟢인데 워크스루·인수인계가 빈 Task {len(empty)}건", empty))
    # C6 (1.2: 에이전트 코드 등록제)
    badname = []
    for t in tasks:
        m = RE_FILE.match(t["name"])
        fid = t["fm"].get("id", "")
        if t["fm_style"] == "fenced":
            badname.append(f"머리말 형식: {t['name']} (```yaml 블록 → 파일 첫 줄부터 --- ~ --- 로 바꿀 것)")
        elif t["fm_style"] == "none":
            badname.append(f"머리말 없음: {t['name']}")
        if not m:
            badname.append(f"파일명 규격 위반: {t['name']}")
        elif fid and fid != m.group(1):
            badname.append(f"id 불일치: {t['name']} (id={fid})")
        mid = RE_ID.match(fid) if fid else None
        if fid and not mid:
            badname.append(f"id 규격 위반: {fid}")
        elif mid and mid.group(1) not in AGENT_CODES:
            badname.append(f"등록되지 않은 에이전트 코드: {fid} (TERMS.md §2에 등록 후 새 AGS-KIT)")
        w = t["fm"].get("work", "")
        if w and not w.startswith("<") and not RE_WORK.match(w):
            badname.append(f"work 키 규격 위반: {task_id_of(t)} ({w})")
    res.append(r("C6", "fail" if badname else "pass", f"이름 규격 위반 {len(badname)}건", badname))
    # C7, C8
    res.append(r("C7", "skip", "에이전트 전용 저장소는 레포 밖 → 각 에이전트 자기 점검"))
    res.append(r("C8", "skip", "글로벌 룰 버전은 자기 보고 → `agentkit.py hash <글로벌 룰 파일>`"))
    # C9
    esc = [task_id_of(t) for t in tasks if t["fm"].get("escalate", "").lower() == "yes"]
    res.append(r("C9", "info" if esc else "pass", f"escalate: yes {len(esc)}건 (HQ 전달 대상)", esc))
    # C10
    hid = []
    for t in tasks:
        txt = (t["sec"].get(4, "") + "\n" + t["sec"].get(5, ""))
        if has_failure(txt) and not has_incident(t["sec"].get(7, "")):
            hid.append(task_id_of(t))
    res.append(r("C10", "warn" if hid else "pass", f"실패 흔적이 있는데 사고 기록이 빈 Task {len(hid)}건", hid))
    # C11
    nonatomic = []
    for c in commits:
        m = re.match(r"^\[(" + RE_ID_ANY.pattern + r")\] ", c["subject"])
        if m and any(not f.startswith("worklog/") for f in c["files"]) and not any(f.startswith("worklog/") for f in c["files"]):
            nonatomic.append(f"{c['hash']} [{m.group(1)}]")
    for newer, older in zip(commits, commits[1:]):
        mn = re.match(r"^\[(" + RE_ID_ANY.pattern + r")\] ", newer["subject"])
        mo = re.match(r"^\[(" + RE_ID_ANY.pattern + r")\] ", older["subject"])
        if mn and mo and mn.group(1) == mo.group(1) and newer["files"] and all(f.startswith("worklog/") for f in newer["files"]):
            nonatomic.append(f"{newer['hash']} [{mn.group(1)}] worklog만 고친 후속 커밋 (commits: [\"self\"]로 한 커밋에)")
    res.append(r("C11", "warn" if nonatomic else "pass", f"원자적 커밋 위반 {len(nonatomic)}건 (코드만 단독 / worklog 후속)", nonatomic))
    # C12
    dup = sorted({i for i in ids if ids.count(i) > 1 and not i.endswith(".md")})
    plan_like = [t for t in tasks if RE_FILE.match(t["name"]) and RE_FILE.match(t["name"]).group(2)]
    dup = [d for d in dup if sum(1 for t in tasks if task_id_of(t) == d and t not in plan_like) > 1]
    res.append(r("C12", "fail" if dup else "pass", f"Task ID 중복 {len(dup)}건", dup))
    # C13
    by_work = {}
    for t in tasks:
        w = t["fm"].get("work", "")
        if w and not w.startswith("<") and t["status"] in OPEN:
            by_work.setdefault(w, []).append(task_id_of(t))
    dupw = [f"{w}: {', '.join(v)}" for w, v in by_work.items() if len(v) > 1]
    res.append(r("C13", "warn" if dupw else "pass", f"같은 work 키로 진행 중 Task 중복 {len(dupw)}건", dupw))
    # C14
    noplan = []
    for t in tasks:
        if t["fm"].get("priority", "").upper() in ("P0", "P1") and t["status"] in ("🟡", "🟢"):
            if t["fm"].get("plan", "").lower() != "confirmed" or not re.search(r"확정\s*:\s*사용자", t["sec"].get(2, "")):
                noplan.append(f"{task_id_of(t)} ({t['fm'].get('priority')}, plan={t['fm'].get('plan','')})")
    res.append(r("C14", "fail" if noplan else "pass", f"P0·P1인데 확정 플랜 없음 {len(noplan)}건", noplan))
    # C15
    noeval = []
    for t in tasks:
        if t["status"] == "🟢":
            ev = t["fm"].get("eval", "").lower()
            if ev not in ("pass", "partial", "bad-case"):
                noeval.append(f"{task_id_of(t)} (eval 없음)")
            elif ev == "bad-case" and not re.search(r"근본 원인\s*:\s*\S", t["sec"].get(8, "")):
                noeval.append(f"{task_id_of(t)} (bad-case 평가 섹션 비어 있음)")
    res.append(r("C15", "fail" if noeval else "pass", f"평가 누락 {len(noeval)}건", noeval))
    # C16
    bad_ids = {task_id_of(t) for t in tasks if t["fm"].get("eval", "").lower() == "bad-case"}
    bc_ids = set(RE_ID_ANY.findall(bad))
    m16 = [f"BADCASES 누락: {i}" for i in sorted(bad_ids - bc_ids)] + [f"bad-case 아닌데 등재: {i}" for i in sorted(bc_ids - bad_ids)]
    res.append(r("C16", "warn" if m16 else "pass", f"배드 케이스 목차 불일치 {len(m16)}건", m16))

    # ---------------- v1.2: 구현 상태 · 결함 · 배포 ----------------
    impls, defs, has_impl, has_def = load_lists(wl)
    tags = scan_impl_tags(root)
    impl_ids = [d["_id"] for d in impls]
    impl_map = {d["_id"]: d for d in impls}
    task_refs = lambda key, rx: {i: task_id_of(t) for t in tasks for i in rx.findall(t["fm"].get(key, ""))}

    # C17 @impl ↔ IMPLEMENTATION.md
    c17 = []
    if tags and not has_impl:
        c17.append("코드에 @impl 표시가 있는데 worklog/IMPLEMENTATION.md 없음 (agentkit.py init)")
    for tg in tags:
        if not tg["id"]:
            c17.append(f"형식 오류 {tg['file']}:{tg['line']} → `@impl IMP-YYYYMMDD-NN <상태>: 설명` ({tg['raw'][:60]})")
        elif tg["id"] not in impl_map:
            c17.append(f"목록에 없는 번호 {tg['id']} ({tg['file']}:{tg['line']})")
        elif field(impl_map[tg["id"]], "상태") != tg["state"]:
            c17.append(f"상태 불일치 {tg['id']}: 코드 {tg['state']} ≠ 목록 {field(impl_map[tg['id']], '상태')}")
    for i in sorted({i for i in impl_ids if impl_ids.count(i) > 1}):
        c17.append(f"목록에 같은 번호 두 번: {i}")
    tagged = {tg["id"] for tg in tags if tg["id"]}
    for d in impls:
        stv = field(d, "상태")
        if stv not in IMPL_STATES:
            c17.append(f"{d['_id']} 상태 값 오류: '{stv}' ({'/'.join(IMPL_STATES)})")
        elif stv in ("MOCK", "PARTIAL", "STATIC") and d["_id"] not in tagged:
            c17.append(f"{d['_id']} {stv}인데 코드에 @impl 표시 없음 (위치: {field(d, '위치')})")
    locs = {}
    for d in impls:
        if field(d, "상태") != "REAL" and field(d, "위치"):
            locs.setdefault(field(d, "위치"), []).append(d["_id"])
    for loc, v in locs.items():
        if len(v) > 1:
            c17.append(f"같은 위치에 번호 여러 개 (중복 등록?): {loc} → {', '.join(v)}")
    for i, tid in task_refs("impl", RE_IMP).items() | task_refs("implements", RE_IMP).items():
        if i not in impl_map:
            c17.append(f"{tid}가 참조한 {i}가 IMPLEMENTATION.md에 없음")
    res.append(r("C17", "fail" if c17 else "pass", f"@impl ↔ IMPLEMENTATION.md 불일치 {len(c17)}건 (코드 표시 {len(tags)}개)", c17))

    # C18 화면 노출 MOCK·PARTIAL
    c18f, c18w = [], []
    for d in impls:
        stv = field(d, "상태")
        if stv in ("MOCK", "PARTIAL") and not field(d, "화면"):
            c18f.append(f"{d['_id']} {stv}: '화면 표시' 칸이 빔 (사용자에게 예시·준비 중임을 어떻게 알리는지 적기)")
        dt = id_date(d["_id"])
        if stv == "MOCK" and dt and (now_local() - dt).days > 30:
            c18w.append(f"{d['_id']} MOCK {(now_local() - dt).days}일째")
    res.append(r("C18", "fail" if c18f else ("warn" if c18w else "pass"), f"화면 노출 MOCK·PARTIAL 문제 {len(c18f)}건 · 오래된 MOCK {len(c18w)}건", c18f + c18w))

    # C19 결함
    c19f, c19w = [], []
    def_ids = [d["_id"] for d in defs]
    def_map = {d["_id"]: d for d in defs}
    for i in sorted({i for i in def_ids if def_ids.count(i) > 1}):
        c19f.append(f"같은 결함 번호 두 번: {i}")
    for d in defs:
        sv, stv, fx = field(d, "심각도").upper(), field(d, "상태").lower(), field(d, "수정")
        if sv not in ("P0", "P1", "P2", "P3"):
            c19f.append(f"{d['_id']} 심각도 값 오류: '{sv}'")
        if stv not in DEF_STATES:
            c19f.append(f"{d['_id']} 상태 값 오류: '{stv}'")
        if sv == "P0" and stv == "open":
            c19f.append(f"{d['_id']} P0 open인데 담당(fixing) 없음 → 수정 Task를 만들고 상태 fixing")
        if stv in ("fixing", "fixed") and not RE_ID_ANY.search(fx):
            c19f.append(f"{d['_id']} {stv}인데 수정 Task 없음")
        dt = id_date(d["_id"])
        if sv == "P1" and stv in ("open", "fixing") and dt and (now_local() - dt).days > 7:
            c19w.append(f"{d['_id']} P1 {stv} {(now_local() - dt).days}일째")
    for i, tid in task_refs("defects_found", RE_DEF).items() | task_refs("fixes", RE_DEF).items():
        if i not in def_map:
            c19f.append(f"{tid}가 참조한 {i}가 DEFECTS.md에 없음")
    if (task_refs("defects_found", RE_DEF) or task_refs("fixes", RE_DEF)) and not has_def:
        c19f.append("Task가 결함 번호를 참조하는데 worklog/DEFECTS.md 없음")
    res.append(r("C19", "fail" if c19f else ("warn" if c19w else "pass"), f"결함 목록 문제 {len(c19f)}건 · 오래된 P1 {len(c19w)}건", c19f + c19w))

    # C20 운영 배포
    c20 = []
    open_p0 = [d["_id"] for d in defs if field(d, "심각도").upper() == "P0" and field(d, "상태").lower() in ("open", "fixing")]
    for t in tasks:
        if not is_deploy(t) or t["status"] not in ("🟡", "🟢"):
            continue
        if t["fm"].get("priority", "").upper() not in ("P0", "P1"):
            c20.append(f"{task_id_of(t)} 운영 배포 Task인데 {t['fm'].get('priority') or '우선순위 없음'} (최소 P1 + 확정 플랜)")
        blocking = [i for i in open_p0 if i not in RE_DEF.findall(t["fm"].get("fixes", ""))]  # 그 P0를 고치는 배포는 허용
        if t["status"] == "🟡" and blocking:
            c20.append(f"{task_id_of(t)} 열린 P0 결함({', '.join(blocking)})이 있는데 배포 진행 중 (이 배포가 고치는 결함이면 fixes:에 적기)")
        refs = RE_IMP.findall(t["fm"].get("impl", ""))
        if any(field(impl_map.get(i, {}), "상태") in ("MOCK", "PARTIAL") for i in refs) and t["status"] == "🟢" \
                and "화면 표시 확인" not in t["sec"].get(5, ""):
            c20.append(f"{task_id_of(t)} MOCK·PARTIAL을 배포했는데 워크스루에 '화면 표시 확인' 기록 없음")
    res.append(r("C20", "fail" if c20 else "pass", f"운영 배포 규칙 위반 {len(c20)}건", c20))

    # ---------------- v1.2: 작업 모드 · git 상태 ----------------
    v12 = v12_adopt_time(root)
    locks, lock_has_mode = parse_locks(now)

    def in_scope(t):
        if t["fm"].get("mode"):
            return True
        s = parse_time(t["fm"].get("started"))
        return bool(v12 and s and s >= v12.replace(second=0))

    # C21 모드 마크
    c21 = []
    if v12 and locks and not lock_has_mode:
        c21.append("NOW.md 잠금 표에 '모드' 열 없음 (v1.2 양식)")
    for l in locks:
        if lock_has_mode and l["mode"] not in MODES:
            c21.append(f"잠금 줄 모드 없음/오류: {l['agent']} {l['task']} ('{l['mode']}')")
    ex = [l for l in locks if l["mode"] in EXCLUSIVE_MODES]
    if ex and len(locks) > 1:
        c21.append(f"단독 모드({', '.join(l['agent'] + ' ' + l['mode'] for l in ex)}) 중인데 다른 잠금 줄이 있음")
    for t in tasks:
        if not in_scope(t) or t["status"] not in ("🟡", "🟢", "🔴"):
            continue
        tid, md = task_id_of(t), t["fm"].get("mode", "").upper()
        if md not in MODES:
            c21.append(f"{tid} 머리말 mode 없음/오류 ('{md}')")
        st, en = marks(t)
        if not st:
            c21.append(f"{tid} 진행 로그에 '▶ 시작 [모드]' 없음")
        for m in st + [e[0] for e in en]:
            if m not in MODES:
                c21.append(f"{tid} 알 수 없는 모드 [{m}]")
        if t["status"] == "🟢" and len(en) < len(st):
            c21.append(f"{tid} 🟢인데 '■ 종료 [모드]'가 시작보다 적음 (시작 {len(st)} · 종료 {len(en)})")
        for m, line in en:
            if m in EXCLUSIVE_MODES and not re.search(r"후속 영향\s*:\s*\S", line):
                c21.append(f"{tid} ■ 종료 [{m}]에 '후속 영향:' 없음")
            if m == "DEPLOY" and not RE_SHA.search(line):
                c21.append(f"{tid} ■ 종료 [DEPLOY]에 '배포 SHA = <sha>' 없음")
    res.append(r("C21", "fail" if c21 else ("pass" if v12 or locks else "pass"), f"작업 모드 마크 위반 {len(c21)}건" + ("" if v12 else " (v1.2 도입 전: mode 있는 Task만)"), c21))

    # C22 주인 없는 미커밋 변경
    if IN_CI:
        res.append(r("C22", "skip", "CI: 작업 트리는 원격과 같음"))
    else:
        dirty = gst["dirty"] if not args.hook else [d for d in gst["dirty"] if d["y"] != " " or d["x"] == "?"]
        orphan = [d for d in dirty if not owned(d["path"], locks)]
        c22 = [f"{d['x']}{d['y']} {d['path']}" for d in orphan]
        res.append(r("C22", "fail" if c22 else ("info" if dirty else "pass"),
                     f"주인 없는 미커밋 변경 {len(c22)}건 (전체 미커밋 {len(dirty)})" +
                     (" → 누구 것인지 확인하고 그 주인이 커밋하거나, NOW.md 잠금 줄 '건드리는 영역'에 적기" if c22 else ""),
                     c22[:15]))

    # C23 🟢인데 커밋 없음
    subjects = git(root, "log", "--all", "--format=%s")
    committed = set(re.findall(r"^\[(" + RE_ID_ANY.pattern + r")\]", subjects, re.M))
    msg_id = None
    if args.msg:  # commit-msg 훅: 지금 만드는 커밋의 TaskID도 커밋된 것으로 본다
        mm = re.match(r"^\[(" + RE_ID_ANY.pattern + r")\] ", read(args.msg).lstrip("﻿"))
        msg_id = mm.group(1) if mm else None
        if msg_id:
            committed.add(msg_id)
    c23 = []
    for t in tasks:
        if t["status"] != "🟢" or not in_scope(t):
            continue
        rel = os.path.relpath(t["path"], root).replace("\\", "/")
        if task_id_of(t) not in committed and (args.hook or rel not in dirty_paths):
            c23.append(f"{task_id_of(t)} 🟢인데 [{task_id_of(t)}] 커밋이 하나도 없음")
    res.append(r("C23", "fail" if c23 else "pass", f"🟢인데 커밋 없는 Task {len(c23)}건", c23))

    # C24 같은 폴더 브랜치 불일치
    if IN_CI or gst["worktree"] or gst["branch"] in ("", "HEAD"):
        res.append(r("C24", "skip", "CI·worktree·detached HEAD에서는 건너뜀"))
    else:
        c24 = [f"{l['agent']} {l['task']} 잠금 브랜치 `{l['branch']}` ≠ 현재 `{gst['branch']}`" for l in locks
               if l["branch"] and ".wt" not in l["branch"] and l["branch"] not in ("-", "—") and l["branch"] != gst["branch"]]
        res.append(r("C24", "fail" if c24 else "pass", f"같은 폴더 브랜치 불일치 {len(c24)}건 (전환 금지, 필요하면 git worktree)", c24))

    # C25 원격보다 앞섬 · 배포 SHA
    c25f, c25w = [], []
    deploying = [l for l in locks if l["mode"] == "DEPLOY"] + [t for t in tasks if t["status"] == "🟡" and is_deploy(t)]
    if not IN_CI and gst["unpushed"] is not None and gst["unpushed"] >= args.ahead_max:
        msg = f"`{gst['branch']}`에 원격 어디에도 없는 커밋 {gst['unpushed']}개" + (f" ({gst['upstream']}보다 {gst['ahead']} 앞섬)" if gst["upstream"] else " (원격 추적 설정 없음. 새 브랜치라면 push 안 된 커밋이 PR에 섞임)")
        (c25f if deploying else c25w).append(msg + (" + DEPLOY 진행 중 → 원격에 없는 코드로 배포 위험" if deploying else ""))
    for t in tasks:
        if t["status"] == "❌":
            continue  # 취소(기록 정정)된 Task의 배포 SHA는 보지 않음
        for m, line in marks(t)[1]:
            sm = RE_SHA.search(line) if m == "DEPLOY" else None
            if not sm:
                continue
            sha = sm.group(1)
            if not git_ok(root, "cat-file", "-e", sha + "^{commit}"):
                c25f.append(f"{task_id_of(t)} 배포 SHA {sha}를 이 레포에서 찾을 수 없음")
            elif not (git(root, "branch", "-r", "--contains", sha).strip() or (IN_CI and git_ok(root, "merge-base", "--is-ancestor", sha, "HEAD"))):
                c25f.append(f"{task_id_of(t)} 배포 SHA {sha}가 원격 브랜치에 없음 (로컬에서만 배포)")
    res.append(r("C25", "fail" if c25f else ("warn" if c25w else "pass"), f"원격 대비 위험 {len(c25f)}건 · 경고 {len(c25w)}건", c25f + c25w))

    # C26 남의 잠금 브랜치에 커밋 (같은 폴더 작업자 분리)
    c26, c26w = [], []
    if not IN_CI and gst["branch"] not in ("", "HEAD"):
        own = {l["agent"] for l in locks if l["branch"] == gst["branch"]}
        start = min([parse_time(l["started"]) for l in locks if l["branch"] == gst["branch"] and parse_time(l["started"])] or [None], key=lambda x: x or datetime.datetime.max)
        if own:
            if args.msg and msg_id and agent_of(msg_id) not in own:
                c26.append(f"지금 커밋 [{msg_id}]: `{gst['branch']}`는 {', '.join(sorted(own))} 잠금 브랜치 → {agent_of(msg_id)}는 자기 잠금·브랜치(git worktree)에서 커밋")
            base = default_branch(root)
            on_base = not base or gst["branch"] in (base, "main", "master")  # origin/HEAD가 다른 브랜치를 가리켜도 main·master는 기본으로 봄
            rng = ["HEAD", "--not", "--remotes"] + ([] if on_base else [base])
            for line in git(root, "log", "--format=%h%x1f%s%x1f%ct", *rng).splitlines():
                h, subj, ct = (line.split("\x1f") + ["", "", "0"])[:3]
                mm = re.match(r"^\[(" + RE_ID_ANY.pattern + r")\]", subj)
                # 기본 브랜치가 아니면 그 브랜치에만 있는 커밋 전부(시각 기록에 기대지 않음), 기본 브랜치면 잠금 시작 뒤 커밋
                late = (not on_base) or start is None or datetime.datetime.fromtimestamp(int(ct)) >= start
                if mm and agent_of(mm.group(1)) not in own and late:
                    if on_base:  # 기본 브랜치: 지난 잠금 기록이 없어 확정할 수 없으므로 경고 (지금 커밋은 위에서 🔴)
                        c26w.append(f"{h} [{mm.group(1)}]: {', '.join(sorted(own))} 잠금 중인 기본 브랜치 `{gst['branch']}`에 잠금 줄 없이 커밋된 것으로 보임 (원격에 아직 없음)")
                    else:
                        c26.append(f"{h} [{mm.group(1)}]가 {', '.join(sorted(own))} 잠금 브랜치 `{gst['branch']}`에 섞임 (push 전 분리 필요)")
    res.append(r("C26", "fail" if c26 else ("warn" if c26w else ("skip" if IN_CI else "pass")), f"남의 잠금 브랜치에 커밋 {len(c26)}건 · 기본 브랜치 경고 {len(c26w)}건", c26 + c26w))

    # C27 목록 Append-Only (지운 줄 = 기록 손실)
    c27 = []
    if v12:
        cur_all = "\n".join(read(os.path.join(root, f)) for f in LIST_FILES)
        since_ts = str(int(v12.timestamp()))
        log27 = git(root, "log", "--no-merges", f"-n{args.since}", f"--since={since_ts}", "-p", "--format=%x1e%h", "--", *LIST_FILES)
        for chunk in log27.split("\x1e")[1:]:
            h = chunk.split("\n", 1)[0].strip()
            for i, l in removed_rows(chunk, cur_all).items():
                c27.append(f"{h} 목록에서 지운 줄 {i}: {l}")
        for i, l in removed_rows(git(root, "diff", "HEAD", "--", *LIST_FILES), cur_all).items():
            c27.append(f"(미커밋) 목록에서 지운 줄 {i}: {l}")
    res.append(r("C27", "fail" if c27 else "pass", f"목록(INDEX·BADCASES·DEFECTS·IMPLEMENTATION) 줄 삭제 {len(c27)}건 (고칠 때는 줄을 지우지 말고 상태를 바꿈)" + ("" if v12 else " (v1.2 도입 전: 건너뜀)"), c27))

    # C28 근거 없는 단정
    c28 = []
    for t in tasks:
        if t["status"] in ("🟡", "🟢", "🔴") and in_scope(t):
            for k in (5, 6, 8):
                for line in unsupported_claims(t["sec"].get(k, "")):
                    c28.append(f"{task_id_of(t)} §{k}: {line}")
    res.append(r("C28", "warn" if c28 else "pass", f"근거 없는 단정(100%·완벽·해결됨·ALL CLEAR) {len(c28)}건 → 같은 줄에 숫자·명령·출력·파일 근거", c28))

    # C29 같은 이름의 배포 설정 중복 (v1.2.1)
    c29, groups = [], {}
    for c in deploy_configs(root):
        groups.setdefault(c["name"], []).append(c)
    for name, cs in sorted(groups.items()):
        if len(cs) > 1:
            diff = len({(tuple(c["crons"]), tuple(c["routes"])) for c in cs}) > 1
            detail = " · ".join(f"`{c['file']}` cron={c['crons'] or '없음'} route={c['routes'] or '없음'}" for c in cs)
            c29.append(f"{name}: 설정 {len(cs)}벌{' (cron·route 다름)' if diff else ''} → {detail}")
    res.append(r("C29", "warn" if c29 else "pass", f"같은 이름의 배포 설정 중복 {len(c29)}건 (어느 파일로 배포됐는지 운영에서 확인하고 하나로 정리)", c29))

    # C30 운영 확인·실측 범위 (v1.2.1, v1.2 도입 뒤 시작한 🟢 Task만)
    c30, lv30 = [], "pass"
    infra = {}
    for chunk in git(root, "log", "--no-merges", f"-n{args.since}", "--format=%x1e%s", "--name-only").split("\x1e")[1:]:
        subj, _, files = chunk.partition("\n")
        hit = [f.strip() for f in files.split("\n") if f.strip() and RE_INFRA.search(f.strip())]
        if hit:
            for i in RE_ID_ANY.findall(subj):
                infra.setdefault(i, set()).update(hit)

    def bump(level):
        nonlocal_lv = {"pass": 0, "warn": 1, "fail": 2}
        return level if nonlocal_lv[level] > nonlocal_lv[lv30] else lv30

    for t in tasks:
        st = parse_time(t["fm"].get("started"))
        if t["status"] != "🟢" or not (v12 and st and st >= v12.replace(second=0)):
            continue
        tid, sec5 = task_id_of(t), t["sec"].get(5, "")
        dep, inf = is_deploy(t), sorted(infra.get(tid, []))
        if dep or inf:
            why = "운영 배포" if dep else "인프라 파일 변경(" + ", ".join(inf[:3]) + ")"
            m = RE_OPS.search(sec5)
            if not m or "<" in m.group(2) or len(re.sub(r"[()\s:：-]", "", m.group(2))) < 4:  # 양식 자리표시자만 있으면 빈 것
                c30.append(f"{tid} {why}인데 워크스루에 '운영 확인: <명령/화면> → <결과>' 또는 '운영 미확인: <이유>' 줄 없음")
                lv30 = bump("fail" if dep else "warn")
            elif not m.group(1) and not RE_EVIDENCE.search(m.group(2)):
                c30.append(f"{tid} '운영 확인'에 명령·출력 근거 없음: {m.group(2)[:60]}")
                lv30 = bump("warn")
        for line in unsupported_measure(sec5):
            c30.append(f"{tid} §5 근거 없는 '실측': {line}")
            lv30 = bump("warn")
    res.append(r("C30", lv30, f"운영 확인·실측 범위 {len(c30)}건 (배포·인프라 판단은 운영 대상에서 확인한 것만 '실측')" + ("" if v12 else " (v1.2 도입 전: 건너뜀)"), c30))

    recent = []
    for line in index.splitlines():
        if line.startswith("|") and RE_ID_ANY.search(line):
            cells = [c.strip() for c in line.strip("|").split("|")]
            recent.append({"status": cells[0], "task": RE_ID_ANY.search(line).group(0), "title": cells[6] if len(cells) > 6 else ""})
        if len(recent) >= 3:
            break
    oi, od = open_items(wl)
    gsum = {"branch": gst["branch"], "upstream": gst["upstream"], "ahead": gst["ahead"], "behind": gst["behind"],
            "unpushed": gst["unpushed"], "dirty": len(gst["dirty"]), "worktree": gst["worktree"]}
    return finish(args, root, res, locks, recent, oi, od, gsum)


def finish(args, root, res, locks, recent, oi, od, gsum):
    icon = {"pass": "🟢", "warn": "🟡", "fail": "🔴", "skip": "⚪", "info": "🔵"}
    summary = {k: sum(1 for x in res if x["level"] == k) for k in icon}
    print(f"agentkit {KIT_VERSION} · {SPEC} · {os.path.basename(root)}")
    for x in res:
        print(f"{icon[x['level']]} {x['id']:<4} {x['msg']}")
        for it in x["items"][:10]:
            print(f"      - {it}")
    print("요약:", " ".join(f"{icon[k]}{v}" for k, v in summary.items()))
    if oi or od:
        print(f"열린 결함 {len(od)} · 남은 구현 {len(oi)} (context에 표시)")
    if args.json:
        data = {"schema": "agentkit-check/2", "kit": KIT_VERSION, "spec": SPEC, "repo": os.path.basename(root),
                "checked_at": now_local().strftime("%Y-%m-%d %H:%M"), "summary": summary, "results": res,
                "active_locks": locks, "recent_tasks": recent, "open_defects": od, "open_impls": oi, "git": gsum}
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("JSON:", args.json)
    if args.summary:
        md = [f"## AGS-CI · agentkit {KIT_VERSION} · {SPEC}", "",
              "요약: " + " ".join(f"{icon[k]}{v}" for k, v in summary.items()), "",
              "| 점검 | 결과 | 내용 |", "|---|---|---|"]
        md += [f"| {x['id']} | {icon[x['level']]} | {x['msg']}" + ("<br>" + "<br>".join(str(i).replace('|', '/') for i in x['items'][:5]) if x['items'] else "") + " |"
               for x in res if x["level"] in ("fail", "warn", "info")] or ["| — | 🟢 | 문제 없음 |"]
        md += ["", f"### 열린 결함 ({len(od)})"] + ([f"- **{d['id']}** {d['severity']} {d['status']} · {d['summary']}" for d in od] or ["- 없음"])
        md += ["", f"### 남은 구현 MOCK·PARTIAL·STATIC·PLANNED ({len(oi)})"] + ([f"- **{i['id']}** {i['state']} · {i['feature']} · {i['location']} · 화면 표시: {i['display'] or '없음'}" for i in oi] or ["- 없음"])
        with open(args.summary, "a", encoding="utf-8") as f:
            f.write("\n".join(md) + "\n")
    if args.strict and summary["fail"]:
        sys.exit(1)


def cmd_doctor(args):
    root = repo_root()
    rows = []

    def add(ok, item, fix="", soft=False):
        rows.append((ok, item, fix, soft))

    add(sys.version_info >= (3, 9), f"Python {sys.version.split()[0]} (3.9 이상 필요)", "Python 3.9+ 설치")
    add(bool(git(root, "rev-parse", "--git-dir")), "git 레포 안에서 실행", "레포 루트에서 실행")
    me = os.path.normcase(os.path.abspath(__file__))
    add(me == os.path.normcase(os.path.join(root, ".agentkit", "agentkit.py")), "키 위치 = <레포>/.agentkit/agentkit.py", "install_agentkit.ps1로 설치")
    add(os.path.isdir(os.path.join(root, "worklog")), "worklog/ 있음", "agentkit.py init")
    for f in ("NOW.md", "INDEX.md", "BADCASES.md", "IMPLEMENTATION.md", "DEFECTS.md"):
        add(os.path.exists(os.path.join(root, "worklog", f)), f"worklog/{f} 있음", "agentkit.py init (있는 파일은 안 건드림)")
    _, has_mode = parse_locks(read(os.path.join(root, "worklog", "NOW.md")))
    add(has_mode, "NOW.md 잠금 표에 '모드' 열 (v1.2)", "templates/NOW.md처럼 '모드' 열 추가", soft=True)
    gi = read(os.path.join(root, ".gitignore"))
    for line in ("worklog/.agentkit-report.json", ".wt/"):
        add(line in gi, f".gitignore에 {line}", "install_agentkit.ps1 (자동 추가)")
    wf = read(os.path.join(root, ".github", "workflows", "agent-contract.yml"))
    add(bool(wf), "CI: .github/workflows/agent-contract.yml 있음", "install_agentkit.ps1 (CI 기본 포함)")
    add(bool(wf) and "continue-on-error: false" in wf, "CI: 🔴면 실패하도록 설정됨 (필수 검사)", "workflow의 continue-on-error를 false로")
    add(bool(re.search(r"AGS_KIT_REF:\s*v\d", wf)) and "AGS_KIT_SHA256" in wf, "CI: AGS-KIT 고정 태그 + 해시 비교 (v1.2)", "install_agentkit.ps1로 CI 갱신")
    hooks = git(root, "rev-parse", "--git-path", "hooks").strip() or ".git/hooks"
    hook = read(os.path.join(root, hooks, "commit-msg"))
    add("agentkit.py check" in hook, "commit-msg 훅이 agentkit check 실행 (v1.2)", "install_agentkit.ps1 (훅 기본 포함)")
    if "agentkit" in read(os.path.join(root, hooks, "pre-commit")):
        add(False, "v1.1 pre-commit 훅이 남아 있음 (C23을 잘못 막음)", "install_agentkit.ps1로 갱신하면 지움", soft=True)
    tracked = git(root, "ls-files", ".agentkit/agentkit.py").strip()
    add(bool(tracked), "키 파일이 git에 커밋됨 (CI가 해시를 비교함)", "[TaskID] agentkit 설치 커밋")
    ga = read(os.path.join(root, ".gitattributes"))
    add(bool(re.search(r"^\*\s+text=auto", ga, re.M)), ".gitattributes에 `* text=auto` (줄바꿈 차이로 무관한 파일이 바뀌는 것 방지)", "`* text=auto` 한 줄 추가 (레포 세션이 커밋)", soft=True)
    hard = [x for x in rows if not x[3]]
    ok = sum(1 for x in hard if x[0])
    print(f"agentkit {KIT_VERSION} doctor · {os.path.basename(root)}")
    for good, item, fix, soft in rows:
        print(("🟢 " if good else ("🟡 " if soft else "🔴 ")) + item + ("" if good else f"   → {fix}"))
    print(f"결과: {ok}/{len(hard)} 통과" + (f" · 권장 {sum(1 for x in rows if x[3] and not x[0])}건" if any(x[3] and not x[0] for x in rows) else ""))
    if args.strict and ok < len(hard):
        sys.exit(1)


def main():
    ap = argparse.ArgumentParser(prog="agentkit", description="anti-gc-sync-pub 계약 검수 키 (AGS-KIT)")
    sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("init"); p.add_argument("--who", default="XX"); p.set_defaults(fn=cmd_init)
    p = sp.add_parser("new-id"); p.add_argument("agent", help="에이전트 코드(" + "|".join(AGENT_CODES) + ") 또는 IMP|DEF"); p.add_argument("--slug"); p.set_defaults(fn=cmd_new_id)
    p = sp.add_parser("context"); p.add_argument("--n", type=int, default=5); p.add_argument("--work"); p.add_argument("--max-chars", type=int, default=12000); p.set_defaults(fn=cmd_context)
    p = sp.add_parser("check"); p.add_argument("--json"); p.add_argument("--summary"); p.add_argument("--strict", action="store_true")
    p.add_argument("--since", type=int, default=50); p.add_argument("--hook", action="store_true"); p.add_argument("--msg", help="commit-msg 훅이 넘기는 메시지 파일"); p.add_argument("--ahead-max", type=int, default=3); p.set_defaults(fn=cmd_check)
    p = sp.add_parser("hash"); p.add_argument("file"); p.set_defaults(fn=cmd_hash)
    p = sp.add_parser("terms"); p.add_argument("file"); p.set_defaults(fn=cmd_terms)
    p = sp.add_parser("collab"); p.add_argument("dir"); p.add_argument("--forbid", action="append", help="공유 문서에 있으면 안 되는 문자열 (여러 번)")
    p.add_argument("--strict", action="store_true"); p.add_argument("--no-ledger", action="store_true"); p.set_defaults(fn=cmd_collab)
    p = sp.add_parser("doctor"); p.add_argument("--strict", action="store_true"); p.set_defaults(fn=cmd_doctor)
    p = sp.add_parser("version"); p.set_defaults(fn=lambda a: print(f"agentkit {KIT_VERSION} ({SPEC})"))
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
