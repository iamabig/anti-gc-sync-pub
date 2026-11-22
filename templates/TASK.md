---
id: T-YYYYMMDD-HHmm-XX
title: 한 줄 제목
status: 🟡
agent: CL | AG | US
repo: <레포 이름>
work: <작업 키>       # 같은 일이면 재시도·이어하기도 같은 키 (CONTRACT §3-1)
continues:           # 이어서 하는 일이면 이전 TaskID
priority: P2         # P0 | P1 | P2 | P3 (CONTRACT §14-1)
plan: draft          # draft | confirmed | n/a  (P0·P1은 confirmed 전 실행 금지)
eval:                # S4에 pass | partial | bad-case
branch: main         # 같은 폴더면 전환 금지. 동시 작업은 git worktree (CONTRACT §12-2)
started: YYYY-MM-DD HH:mm KST
updated: YYYY-MM-DD HH:mm KST
commits: []          # 작업 커밋 자신은 비워 두거나 ["self"] (CONTRACT §6)
related: []          # 관련 Task ID, 이슈 파일
escalate: no         # 레포 밖 영향이 있으면 yes (CONTRACT §7)
---

# <TaskID> · <제목>

## 1. 목표
- 무엇을, 왜. 완료 기준 한두 줄.

## 2. 계획
- 접근 방법. 바꿀 파일과 범위. 대안이 있었다면 왜 이 방법인지.
- (P0·P1) 확정: 사용자 YYYY-MM-DD HH:mm

## 3. 체크리스트
- [ ] 단계 1
- [ ] 단계 2
- [ ] 검증

## 4. 진행 로그
| 시각 (KST) | 에이전트 | 내용 |
|---|---|---|
| HH:mm | XX | 시작 |

## 5. 워크스루 (결과·검증 증적)
- **바꾼 것**: 파일과 변경 요약
- **검증 방법**: 실행한 명령
- **실제 결과**: 출력 요약 (비밀값 제외)
- **남은 것 / 검증 못 한 것**:

## 6. 인수인계
- 다음 에이전트(또는 다음 세션)가 이것만 읽고 이어갈 수 있게.
- 막혔다면: 필요한 결정과 누가 결정해야 하는지.

## 7. 사고 기록 (5-Step. CLI·API·테스트 실패가 있었다면 필수, 없으면 "없음")
| ① 증상 | ② 근본 원인 | ③ 조치 | ④ 실측 검증 | ⑤ 재발 방지 |
|---|---|---|---|---|

## 8. 평가 (CONTRACT §14-3. bad-case면 필수, 아니면 한 줄)
- 판정: pass | partial | bad-case
- 유형: (bad-case일 때) PLAN_DEVIATION · FALSE_DONE · REWORK · SCOPE_BREACH · CONTEXT_LOSS · DUPLICATE_WORK · CONFLICT · TIME_ERROR · OTHER
- 무슨 일이 있었나:
- 근본 원인:
- 교훈:
- 재발 방지:
