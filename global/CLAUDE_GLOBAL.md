<!-- anti-gc-sync-pub v1.1 · Claude 글로벌 룰 (설치: ~/.claude/CLAUDE.md) -->
# 멀티에이전트 공통 계약 v1.1 (anti-gc-sync-pub)

**적용 범위:** 작업 폴더가 `<REPOS_ROOT>` 아래 레포일 때만 적용합니다. 그 밖의 프로젝트에서는 이 절을 무시합니다.
원본: https://github.com/iamabig/anti-gc-sync-pub (태그 v1.1) · 레포 `AGENTS.md`와 충돌하면 더 엄격한 쪽을 따릅니다.

이 레포에서는 Claude와 Antigravity가 `worklog/`로 서로 소통하며 함께 작업합니다. `worklog/`는 **컨텍스트 효율 도구**입니다: 전체를 읽지 말고 목차로 필요한 조각만 불러옵니다.

1. **시작할 때 (컨텍스트 팩)**: 레포에 검수 키가 있으면 `python .agentkit/agentkit.py context`를 실행해 그 출력만 읽습니다. 없으면 `worklog/NOW.md` 전체 → `INDEX.md` 최근 5줄 → 🟡/🔴 Task와 이번 `work` 키 Task → `BADCASES.md` 최근 5줄만 읽습니다. 전체 Task를 한꺼번에 읽지 않습니다. `worklog/`가 없으면 양식대로 만듭니다 (`agentkit.py init`).
2. **동시 작업**: NOW.md "작업 중 에이전트"에 자기 줄(CL, Task ID, 브랜치, 건드리는 영역, 시작 시각)을 적습니다. 상대가 같은 영역을 잡고 있으면 기다리거나 다른 작업을 합니다. **같은 레포 폴더에서는 브랜치를 전환하지 않습니다.** 동시에 다른 브랜치가 필요하면 `git worktree add .wt/<TaskID> -b feature/<TaskID>`. 끝나면 자기 줄을 지웁니다.
3. **기록 위치**: 계획, 체크리스트, 워크스루, 평가는 `worklog/tasks/YYYY-MM/<TaskID>_<slug>.md` 한 파일에 씁니다. 개인 메모리에만 남긴 기록은 인정되지 않습니다.
4. **Task ID와 중복 방지**: `T-YYYYMMDD-HHmm-CL` (기록 직전 OS 시계. Windows는 PowerShell `Get-Date -Format "yyyy-MM-dd HH:mm"`, 모델 추정 시각 금지). 검수 키가 있으면 `agentkit.py new-id CL`로 만듭니다. 작업 1건 = 파일 1개. 같은 일을 다시 하거나 이어 하면 새 Task에 같은 `work` 키와 `continues:`를 적습니다. 같은 `work` 키의 진행 중 Task가 있으면 새로 만들지 말고 합류합니다. 커밋 첫 줄 `[<TaskID>] 요약`. `commits:`는 비우거나 `["self"]`.
5. **우선순위와 확정 플랜**: `priority`를 P0~P3로 적습니다. **P0·P1은 계획을 사용자에게 확정받기 전(`plan: confirmed`)에 코드·설정을 바꾸지 않습니다.** 확정 뒤 계획을 바꾸면 다시 확정받습니다.
6. **보고 전에 기록**: 사용자에게 보고하기 전에 작업 파일과 NOW.md를 먼저 갱신합니다. 결정과 결과는 대화에 쌓지 말고 즉시 파일에 적습니다.
7. **완료(🟢)**: 워크스루(실제 검증 출력) + 인수인계 + **평가(`eval`: pass / partial / bad-case)** 가 있을 때만. bad-case면 Task §8에 유형·원인·교훈·재발 방지를 쓰고 `BADCASES.md` 맨 위에 한 줄. 실패가 있었다면 사고 기록(5-Step)도. 검수 키가 있으면 커밋 전에 `agentkit.py check`. 코드와 worklog는 **같은 커밋**에.
8. **범위**: 이 레포 폴더 안에서만 작업합니다. 레포 밖에 영향이 있는 문제는 작업 파일에 `escalate: yes`로 표시하고 사용자에게 "HQ 전달 필요"라고 알립니다.
9. **자원 (8GB 기기)**: 자기가 띄운 node(dev 서버, watch, 빌드, npx MCP)는 작업이 끝나면 끕니다. 켜 둘 때는 NOW.md에 PID·포트·용도를 적습니다. `--max-old-space-size` 1024MB 이하, 전역 `NODE_OPTIONS` 힙 설정 금지, dev 서버는 레포당 1개, 여러 레포 빌드·배포 동시 실행 금지. 남이 띄운 것은 끄지 않습니다.
10. **세션 전환**: 대화가 길어지면 인수인계를 쓰고 새 세션에서 컨텍스트 팩만으로 다시 시작합니다.
11. **상태 값**: 🟡 진행 · 🟢 완료 · 🔴 막힘(이유 필수) · ⚪ 보류 · ❌ 취소(사유 필수)

### worklog 양식 (요약, 전체는 원본 `templates/`)
- `NOW.md`: 갱신 시각·갱신자 / 🔒 작업 중 에이전트 표 / 🟡 진행 중 / 🔴 막힘 / ⏭️ 다음 할 일 / ✅ 최근 완료 3건 / ⚠️ 알아야 할 것
- `INDEX.md`: `상태 | Task ID(링크) | 시작 | 에이전트 | 우선순위 | 작업 키 | 제목 | 평가`, 최신이 위
- `BADCASES.md`: `일시 | Task ID | 에이전트 | 유형 | 한 줄 교훈`, 최신이 위
- 작업 파일 머리말(**파일 첫 줄부터 `---` ~ `---`**, 코드펜스 금지): `id, title, status, agent, repo, work, continues, priority, plan, eval, branch, started, updated, commits, related, escalate` / 섹션: 1 목표 · 2 계획 · 3 체크리스트 · 4 진행 로그 · 5 워크스루 · 6 인수인계 · 7 사고 기록 · 8 평가
<!-- /anti-gc-sync-pub v1.1 -->
