<!-- anti-gc-sync-pub v1.0 · Claude 글로벌 룰 (설치: ~/.claude/CLAUDE.md) -->
# 멀티에이전트 공통 계약 v1.0 (anti-gc-sync-pub)

**적용 범위:** 작업 폴더가 `<REPOS_ROOT>` 아래 레포일 때만 적용합니다. 그 밖의 프로젝트에서는 이 절을 무시합니다.
원본: https://github.com/iamabig/anti-gc-sync-pub (태그 v1.0) · 레포 `AGENTS.md`와 충돌하면 더 엄격한 쪽을 따릅니다.

이 레포에서는 Claude와 Antigravity가 `worklog/`로 서로 소통하며 함께 작업합니다.

1. **시작할 때**: `worklog/NOW.md` → `worklog/INDEX.md` 최근 5줄 → 관련 작업 파일 순서로 읽습니다. NOW.md의 "작업 중 에이전트"를 먼저 확인합니다. `worklog/`가 없으면 아래 양식대로 만듭니다.
2. **동시 작업**: 시작하면 NOW.md "작업 중 에이전트"에 자기 줄(CL, Task ID, 브랜치, 건드리는 영역, 시작 시각)을 적습니다. 상대가 같은 영역을 잡고 있으면 기다리거나 다른 작업을 합니다. 동시 작업이면 `feature/<TaskID>` 브랜치를 씁니다. 끝나면 자기 줄을 지웁니다.
3. **기록 위치**: 계획, 체크리스트, 워크스루는 `worklog/tasks/YYYY-MM/<TaskID>_<slug>.md`에 씁니다. 개인 메모리에만 남긴 기록은 인정되지 않습니다.
4. **Task ID**: `T-YYYYMMDD-HHmm-CL` (OS 로컬 시각. Windows에서는 PowerShell `Get-Date`). 커밋 첫 줄 `[<TaskID>] 요약`.
5. **보고 전에 기록**: 사용자에게 보고하기 전에 작업 파일과 NOW.md를 먼저 갱신합니다.
6. **완료(🟢)**: 워크스루(실제 검증 출력) + 인수인계가 있을 때만. 실패가 있었다면 사고 기록(5-Step)도 씁니다. 코드와 worklog는 **같은 커밋**에.
7. **범위**: 이 레포 폴더 안에서만 작업합니다. 레포 밖에 영향이 있는 문제는 작업 파일에 `escalate: yes`로 표시하고 사용자에게 "HQ 전달 필요"라고 알립니다.
8. **상태 값**: 🟡 진행 · 🟢 완료 · 🔴 막힘(이유 필수) · ⚪ 보류 · ❌ 취소(사유 필수)

### worklog 양식 (요약)
- `NOW.md`: 갱신 시각·갱신자 / 🔒 작업 중 에이전트 표(에이전트 | Task ID | 브랜치 | 영역 | 시작) / 🟡 진행 중 / 🔴 막힘 / ⏭️ 다음 할 일 / ✅ 최근 완료 3건 / ⚠️ 이 레포에서 알아야 할 것
- `INDEX.md`: 표 `상태 | Task ID(링크) | 시작 | 에이전트 | 제목 | 커밋`, 최신이 위
- 작업 파일: 머리말(`id, title, status, agent, repo, branch, started, updated, commits, related, escalate`) + 1 목표 · 2 계획 · 3 체크리스트 · 4 진행 로그 · 5 워크스루 · 6 인수인계 · 7 사고 기록
- 전체 양식: 원본 저장소 `templates/`
<!-- /anti-gc-sync-pub v1.0 -->
