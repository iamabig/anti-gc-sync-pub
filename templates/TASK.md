---
id: T-YYYYMMDD-HHmm-XX
title: 한 줄 제목
status: 🟡
agent: XX            # TERMS.md §2에 등록된 코드 (CL | AG | US …)
repo: <레포 이름>
work: <작업 키>       # 같은 일이면 재시도·이어하기도 같은 키 (CONTRACT §3-1)
continues:           # 이어서 하는 일이면 이전 TaskID
mode: CODE           # THINK | CODE | SENSITIVE | MAINT | DEPLOY | REVIEW (CONTRACT §12-4)
deploy: no           # 운영 배포가 포함되면 yes → 최소 P1 (CONTRACT §14-1)
priority: P2         # P0 | P1 | P2 | P3 (CONTRACT §14-1)
plan: draft          # draft | confirmed | n/a  (P0·P1은 confirmed 전 실행 금지)
eval:                # S4에 pass | partial | bad-case
branch: main         # 같은 폴더면 전환 금지. 동시 작업은 git worktree (CONTRACT §12-2)
started: YYYY-MM-DD HH:mm KST
updated: YYYY-MM-DD HH:mm KST
commits: []          # 작업 커밋 자신은 비워 두거나 ["self"] (CONTRACT §6)
impl: []             # 이 Task가 만들거나 남긴 IMP 번호 (CONTRACT §16)
implements: []       # 이 Task가 실제화한 IMP 번호
defects_found: []    # 발견한 DEF 번호 (CONTRACT §17)
fixes: []            # 고친 DEF 번호
related: []          # 관련 Task ID, 이슈 파일
escalate: no         # 레포 밖 영향이 있으면 yes (CONTRACT §7)
---

# <TaskID> · <제목>

## 1. 목표
- 무엇을, 왜. 완료 기준 한두 줄.

## 2. 계획
### 사전 분석
- 범위:
- 영향 받는 파일/화면:
- 위험:
- 구현 상태 계획: (REAL / PARTIAL / MOCK / STATIC / PLANNED, 남길 하드코딩이 있으면 IMP 번호)
### 접근
- 접근 방법. 바꿀 파일과 범위. 대안이 있었다면 왜 이 방법인지.
- (P0·P1) 확정: 사용자 YYYY-MM-DD HH:mm
- 사전 점검: `agentkit.py health` → <점수>점 (지문 <12자리>) (CONTRACT §22, 시작 전에 실행)

## 3. 체크리스트 (WBS)
| 번호 | 작업 | 산출물 | 구현 상태 | 완료 |
|---|---|---|---|---|
| 1 | | | | ☐ |
| 2 | 검증 (테스트 실행) | 테스트 출력 | — | ☐ |

## 4. 진행 로그
- HH:mm ▶ 시작 [CODE] 무엇을 시작
- HH:mm ■ 종료 [CODE] 후속 영향: (SENSITIVE·MAINT·DEPLOY는 필수. DEPLOY는 `배포 SHA = <sha>`도)

## 5. 워크스루 (결과·검증 증적)
- **바꾼 것**: 파일과 변경 요약
- **검증 방법**: 실행한 명령
- **실제 결과**: 출력 요약 (비밀값 제외)
- **테스트 결과**: 실행한 테스트와 통과 여부 (예: `npm run test:all` 94건 중 94 통과. 안 돌렸으면 이유)
- **운영 확인**: (배포·인프라를 다뤘을 때 필수, CONTRACT §20) `운영 확인: <읽기 전용 명령/화면> → <결과>` 또는 `운영 미확인: <이유> → <누가 확인할지>`
- **사후 점검**: `agentkit.py health` → <점수>점 (지문 <12자리>) (끝낸 뒤 실행. 🔴가 있거나 80점 미만이면 🟢 금지)
- **공유 구역**: `share: #NNNN` (이 Task의 PLAN·WALK·TURN 번호, CONTRACT §21)
- **남은 것 / 검증 못 한 것**: ("실측"이라고 쓸 때는 명령을 붙이고 레포·운영을 구분)
### 사후 분석
- 계획 대비 실제:
- 남은 MOCK·PARTIAL: (IMP 번호, 없으면 "없음". MOCK·PARTIAL을 배포했다면 "화면 표시 확인" 결과)
- 배포 여부: (안 함 / 함 → 배포 SHA)

## 6. 인수인계
- 다음 에이전트(또는 다음 세션)가 이것만 읽고 이어갈 수 있게.
- 막혔다면: 필요한 결정과 누가 결정해야 하는지.

## 7. 사고 기록 (5-Step. CLI·API·테스트 실패가 있었다면 필수, 없으면 "없음")
| ① 증상 | ② 근본 원인 | ③ 조치 | ④ 실측 검증 | ⑤ 재발 방지 |
|---|---|---|---|---|

## 8. 평가 (CONTRACT §14-3. bad-case면 필수, 아니면 한 줄)
- 판정: pass | partial | bad-case
- 유형: (bad-case일 때) PLAN_DEVIATION · FALSE_DONE · REWORK · SCOPE_BREACH · CONTEXT_LOSS · DUPLICATE_WORK · CONFLICT · TIME_ERROR · SILENT_FALLBACK · OTHER
- 무슨 일이 있었나:
- 근본 원인:
- 교훈:
- 재발 방지:
