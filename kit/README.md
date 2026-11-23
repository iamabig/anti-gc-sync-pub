# 🔑 AGS-KIT — 멀티에이전트 계약 검수 키

| 항목 | 값 |
|---|---|
| 키 버전 | 1.2.1 |
| 맞춘 규격 | `anti-gc-sync-pub` v1.2.1 (이 저장소의 태그가 원본) |
| 실행 환경 | Python 3.9 이상, **표준 라이브러리만** (설치할 것 없음, node 불필요) |
| 배포 | **사용자가** 각 레포에 설치합니다. 에이전트 본부(AGS-HQ)는 키를 만들고 관리만 합니다 |

## 1. 이 키가 하는 일

1. **컨텍스트 통제** (`context`): 새 세션이 읽을 내용을 정해진 크기의 팩 하나로 뽑습니다. 순서: **git 상태 → NOW → 열린 결함·남은 구현 → 진행 중 Task → 배드 케이스 → INDEX**.
2. **번호 발급** (`new-id`): 겹치지 않는 Task ID(등록된 에이전트 코드), `IMP-`·`DEF-` 번호.
3. **검수** (`check`): 계약 C1~C30. 신호등 출력, 대시보드·CI용 JSON(`agentkit-check/2`), CI Job Summary(마크다운).
4. **시작 도우미** (`init`): worklog 양식 5종(NOW, INDEX, BADCASES, IMPLEMENTATION, DEFECTS). 있는 파일은 건드리지 않습니다.
5. **자기 보고** (`hash`), **용어 비교** (`terms TERMS.md`), **설치 점검** (`doctor`).
6. **에이전트 간 문서 점검** (`collab <공통 구역 폴더> --forbid <쓰면 안 되는 문자열>`): TURN·REPORT의 머리 표, 근거 표시, 단정, 금지 문자열, 서명 위치, Append-Only(장부 `.collab-ledger.json`), 턴 순서, 이름 (R1~R8, CONTRACT §19-1).

## 2. 설치·갱신 (사용자)

이 저장소를 내려받은 폴더에서:

```powershell
.\kit\install\install_agentkit.ps1 -Repo <레포경로> -WhatIf   # 먼저 미리보기
.\kit\install\install_agentkit.ps1 -Repo <레포경로>
```
- 키 복사(LF 고정), AGS-CI(고정 태그 + 해시), `.gitignore` 2줄, `commit-msg` 훅, 없는 worklog 양식, `doctor` 점검까지 한 번에. **커밋·push는 하지 않습니다.**
- 여러 레포: `.\kit\install\install_all.ps1 -Registry <레포 목록 표.md> -ReposRoot <레포 루트> -WhatIf` (계정·폴더별로 묶어 실행, `-Account`·`-Only`로 고르기)
- 설치 뒤 그 레포 창의 에이전트가 `[TaskID] AGS-KIT 1.2.1 설치`로 커밋합니다. push는 사용자 승인 후.
- v1.1에서 올리면: 옛 `pre-commit` 훅은 지워지고 `commit-msg` 훅으로 바뀝니다. NOW.md 잠금 표에 `모드` 열을 추가하세요 (`doctor` 🟡로 알려 줌).

## 3. 사용법 (레포 세션)

| 시점 | 명령 | 뜻 |
|---|---|---|
| **S0 세션 시작** | `python .agentkit/agentkit.py context` | 컨텍스트 팩 (이것만 읽는다) |
| 특정 일 이어하기 | `python .agentkit/agentkit.py context --work <작업키>` | 그 작업 키의 Task까지 |
| S1 작업 시작 | `python .agentkit/agentkit.py new-id CL --slug fix-login` | Task ID와 파일 경로 |
| 하드코딩을 남길 때 | `python .agentkit/agentkit.py new-id IMP` | `IMP-YYYYMMDD-NN` |
| 결함을 찾았을 때 | `python .agentkit/agentkit.py new-id DEF` | `DEF-YYYYMMDD-NN` |
| **S4 커밋 전** | `python .agentkit/agentkit.py check` | 🔴가 있으면 고치고 커밋 |
| 설치 확인 | `python .agentkit/agentkit.py doctor` | 설치가 빠짐없는지 |
| 글로벌 룰 보고 | `python .agentkit/agentkit.py hash <글로벌 룰 파일>` | 버전 + 해시 |

## 4. 점검 항목 (check)

| ID | 등급 | 내용 |
|---|---|---|
| C1 | 🟡 | worklog 도입 이후 커밋 중 `[TaskID]` 없는 것 |
| C2 | 🟡 | INDEX ↔ 작업 파일 1:1 |
| C3 | 🟡 | 72시간 넘게 갱신 없는 🟡 |
| C4 | 🟡 | NOW.md가 마지막 작업 커밋보다 오래됨 |
| C5 | 🔴 | 🟢인데 워크스루·인수인계가 빔 (양식 문구만 있어도 빈 것) |
| C6 | 🔴 | 파일명·ID·work 키 규격, **등록되지 않은 에이전트 코드** |
| C7·C8 | ⚪ | 레포 밖이라 건너뜀 (자기 점검·`hash`) |
| C9 | 🔵 | `escalate: yes` 목록 |
| C10 | 🟡 | 실패 흔적이 있는데 사고 기록이 빔 |
| C11 | 🟡 | 코드만 단독 커밋, worklog만 고친 후속 커밋 |
| C12 | 🔴 | Task ID 중복 |
| C13 | 🟡 | 같은 work 키로 진행 중 Task가 둘 이상 |
| C14 | 🔴 | P0·P1인데 확정 플랜 없음 |
| C15 | 🔴 | 🟢인데 `eval` 없음, bad-case인데 근본 원인 빔 |
| C16 | 🟡 | bad-case ↔ BADCASES.md 불일치 |
| **C17** | 🔴 | `@impl` ↔ IMPLEMENTATION.md (형식, 없는 번호, 중복, 상태 불일치, 코드 표시 누락, 같은 위치 중복) |
| **C18** | 🔴/🟡 | MOCK·PARTIAL "화면 표시" 빔 / 30일 넘은 MOCK |
| **C19** | 🔴/🟡 | 결함 번호·중복·없는 참조, P0 open 담당 없음, 수정 Task 없음 / P1 7일 초과 |
| **C20** | 🔴 | 배포 Task가 P1 미만, 열린 P0 중 배포(그 P0를 고치는 배포 제외), MOCK 배포인데 화면 표시 확인 없음 |
| **C21** | 🔴 | 모드 마크 누락·오류, 단독 모드 중 다른 잠금, SENSITIVE·MAINT·DEPLOY 후속 영향 없음, DEPLOY 배포 SHA 없음 |
| **C22** | 🔴 | 잠금 영역 밖의 미커밋 변경 (로컬만) |
| **C23** | 🔴 | 🟢인데 `[TaskID]` 커밋 없음 |
| **C24** | 🔴 | 잠금 브랜치 ≠ 현재 브랜치 (같은 폴더, 로컬만) |
| **C25** | 🟡/🔴 | 원격 어디에도 없는 커밋 3개 이상 (DEPLOY 중이면 🔴) / 배포 SHA가 원격에 없음 🔴 |
| **C26** | 🔴/🟡 | 남이 잠근 브랜치에 커밋 (같은 폴더 작업자 분리, 로컬·훅). 기본 브랜치의 원격에 없는 지난 커밋은 🟡, 훅의 지금 커밋은 🔴 |
| **C27** | 🔴 | 목록(INDEX·BADCASES·DEFECTS·IMPLEMENTATION)의 줄 삭제 (Append-Only) |
| **C28** | 🟡 | 근거 없는 "100%·완벽·해결됨·ALL CLEAR" |
| **C29** | 🟡 | 같은 이름의 배포 설정(wrangler `name`)이 두 파일 이상. cron·route가 다르면 표시 |
| **C30** | 🔴/🟡 | 운영 배포 🟢인데 워크스루에 `운영 확인:`/`운영 미확인:` 없음 🔴 · 인프라 파일 변경인데 없음, 운영 확인에 명령 없음, 명령 없는 "실측" 🟡 (CONTRACT §20) |

- C17~C21·C23은 v1.2 도입(IMPLEMENTATION.md·DEFECTS.md 첫 커밋) 뒤 Task부터. 그 전 Task는 머리말에 `mode`가 있을 때만.
- `--hook --msg <파일>`: commit-msg 훅용. 이번 커밋에 안 들어가는 변경만 C22로 보고, 지금 커밋의 `[TaskID]`를 C23에서 커밋된 것으로 봅니다.

## 5. JSON 출력 (`agentkit-check/2`)

```json
{
  "schema": "agentkit-check/2", "kit": "1.2.1", "spec": "anti-gc-sync-pub v1.2.1",
  "repo": "<레포>", "checked_at": "YYYY-MM-DD HH:mm",
  "summary": {"pass": 0, "warn": 0, "fail": 0, "skip": 0, "info": 0},
  "results": [{"id": "C1", "level": "pass|warn|fail|skip|info", "msg": "...", "items": ["..."]}],
  "active_locks": [{"agent": "CL", "task": "T-...", "mode": "CODE", "branch": "main", "area": "...", "started": "..."}],
  "recent_tasks": [{"status": "🟡", "task": "T-...", "title": "..."}],
  "open_defects": [{"id": "DEF-...", "severity": "P0", "status": "open", "summary": "...", "fix_task": ""}],
  "open_impls": [{"id": "IMP-...", "state": "MOCK", "feature": "...", "location": "파일:줄", "display": "...", "until": "..."}],
  "git": {"branch": "main", "upstream": "origin/main", "ahead": 0, "behind": 0, "unpushed": 0, "dirty": 0, "worktree": false}
}
```
- `agentkit-check/1`에서 바뀐 것: 위 세 키(`open_defects`, `open_impls`, `git`)와 `active_locks[].mode` 추가 (Antigravity 대시보드 요청 CQ2). 기존 키는 그대로입니다.

## 6. 오차 방지 장치

| 장치 | 언제 | 막는 것 |
|---|---|---|
| `commit-msg` 훅 | 커밋할 때 (로컬) | 🔴면 커밋 멈춤. 주인 없는 변경·브랜치 불일치·원격 없는 배포도 여기서 |
| AGS-CI `agent-contract` | push·PR 때 | 훅을 건너뛴 커밋도 🔴면 실패. 레포의 키 사본이 고정 태그와 다르면 실패 |
| `doctor` | 설치·갱신 직후 | 설치 누락, CI 꺼짐·버전 미고정, 훅 없음, `.gitattributes` 권장 |

CI 운영: [ci/CI_PLAN.md](ci/CI_PLAN.md) · 양식: [ci/agent-contract.yml](ci/agent-contract.yml)
