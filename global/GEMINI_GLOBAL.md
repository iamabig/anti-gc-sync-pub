<!-- anti-gc-sync-pub v1.2.2 · Antigravity 글로벌 룰 (설치: ~/.gemini/GEMINI.md) -->
# 멀티에이전트 공통 계약 v1.2.2 (anti-gc-sync-pub)

**적용 범위:** 작업 폴더가 `<REPOS_ROOT>` 아래 레포일 때만 적용합니다. 그 밖의 프로젝트에서는 이 절을 무시합니다.
원본: https://github.com/iamabig/anti-gc-sync-pub (태그 v1.2.2) · 레포 `AGENTS.md`와 충돌하면 더 엄격한 쪽을 따릅니다.

이 레포에서는 Antigravity와 Claude가 `worklog/`로 서로 소통하며 함께 작업합니다. `worklog/`는 **컨텍스트 효율 도구**입니다: 전체를 읽지 말고 목차로 필요한 조각만 불러옵니다.

1. **시작할 때 (컨텍스트 팩)**: 레포에 검수 키가 있으면 `python .agentkit/agentkit.py context`를 실행해 그 출력만 읽습니다. 맨 위 **git 상태**의 ⚠️(주인 없는 미커밋, 원격에 없는 커밋, 브랜치 불일치)와 **열린 결함·남은 구현**부터 확인합니다. 없으면 `worklog/NOW.md` 전체 → `INDEX.md` 최근 5줄 → 🟡/🔴 Task와 이번 `work` 키 Task → `BADCASES.md` 최근 5줄만 읽습니다. 전체 Task를 한꺼번에 읽지 않습니다. `worklog/`가 없으면 양식대로 만듭니다 (`agentkit.py init`).
2. **동시 작업**: NOW.md "작업 중 에이전트"에 자기 줄(AG, Task ID, **모드**, 브랜치, 건드리는 영역(경로·폴더·파일 이름), 시작 시각)을 적습니다. 상대가 같은 영역을 잡고 있으면 기다리거나 다른 작업을 합니다. **같은 레포 폴더에서는 브랜치를 전환하지 않습니다.** 동시에 다른 브랜치가 필요하면 `git worktree add .wt/<TaskID> -b feature/<TaskID>`. 끝나면 자기 줄을 지웁니다.
3. **기록 위치**: implementation_plan / task / walkthrough 산출물은 계획 수립·체크리스트 진행·완료 시점마다 `worklog/tasks/YYYY-MM/<TaskID>_<slug>.md`의 계획 / 체크리스트 / 워크스루 섹션에 반영합니다. brain에만 남긴 기록은 인정되지 않습니다 (세션이 바뀌면 이어지지 않음).
4. **Task ID와 중복 방지**: `T-YYYYMMDD-HHmm-AG` (기록 직전 OS 시계. Windows는 PowerShell `Get-Date -Format "yyyy-MM-dd HH:mm"`, 모델 추정 시각 금지). 검수 키가 있으면 `agentkit.py new-id AG`로 만듭니다. 작업 1건 = 파일 1개. 같은 일을 다시 하거나 이어 하면 새 Task에 같은 `work` 키와 `continues:`를 적습니다. 같은 `work` 키의 진행 중 Task가 있으면 새로 만들지 말고 합류합니다. 커밋 첫 줄 `[<TaskID>] 요약`. `commits:`는 비우거나 `["self"]`.
5. **우선순위와 확정 플랜**: `priority`를 P0~P3로 적습니다. **운영 배포, 법적·금융 고지 문구 변경은 최소 P1**입니다. **P0·P1은 계획을 사용자에게 확정받기 전(`plan: confirmed`)에 코드·설정을 바꾸지 않습니다.** 확정 뒤 계획을 바꾸면 다시 확정받습니다.
6. **보고 전에 기록**: 사용자에게 보고하기 전에 작업 파일과 NOW.md를 먼저 갱신합니다. 결정과 결과는 대화에 쌓지 말고 즉시 파일에 적습니다.
7. **완료(🟢)**: 워크스루(실제 검증 출력 + **테스트 결과** + 사후 분석) + 인수인계 + **평가(`eval`: pass / partial / bad-case)** 가 있을 때만. bad-case면 Task §8에 유형·원인·교훈·재발 방지를 쓰고 `BADCASES.md` 맨 위에 한 줄. 실패가 있었다면 사고 기록(5-Step)도. 검수 키가 있으면 커밋 전에 `agentkit.py check`. 코드와 worklog는 **같은 커밋**에. `[TaskID]` 커밋 없이 🟢로 보고하지 않습니다.
8. **범위**: 이 레포 폴더 안에서만 작업합니다. 레포 밖에 영향이 있는 문제는 작업 파일에 `escalate: yes`로 표시하고 사용자에게 "HQ 전달 필요"라고 알립니다.
9. **자원 (8GB 기기)**: 자기가 띄운 node(dev 서버, watch, 빌드, npx MCP)는 작업이 끝나면 끕니다. 켜 둘 때는 NOW.md에 PID·포트·용도를 적습니다. `--max-old-space-size` 1024MB 이하, 전역 `NODE_OPTIONS` 힙 설정 금지, dev 서버는 레포당 1개, 여러 레포 빌드·배포 동시 실행 금지. 남이 띄운 것은 끄지 않습니다.
10. **세션 전환**: 대화가 길어지면 인수인계를 쓰고 새 세션에서 컨텍스트 팩만으로 다시 시작합니다.
11. **상태 값**: 🟡 진행 · 🟢 완료 · 🔴 막힘(이유 필수) · ⚪ 보류 · ❌ 취소(사유 필수)

12. **작업 모드**: 시작과 끝에 진행 로그 `▶ 시작 [모드]` / `■ 종료 [모드] 후속 영향: …`. 모드 `THINK`(설계, 코드 변경 없음) · `CODE` · `SENSITIVE`(DB·시크릿·권한·인프라) · `MAINT`(캐시·의존성·빌드 환경) · `DEPLOY`(운영 배포) · `REVIEW`(읽기만). **SENSITIVE·MAINT·DEPLOY는 단독**: 다른 잠금 줄이 있으면 기다리고, 위험 단계 직전에 NOW.md를 다시 읽고, 종료에 후속 영향을 반드시 적습니다.
13. **하드코딩·목업**: 임시 하드코딩은 그 자리에 `// @impl IMP-YYYYMMDD-NN <MOCK|PARTIAL|STATIC|PLANNED>: 한 줄 설명`(번호는 `agentkit.py new-id IMP`)을 달고 `worklog/IMPLEMENTATION.md`에 등록합니다(화면 표시·실제화 조건). MOCK·PARTIAL에 "AI/LLM 분석", "실시간" 같은 실제 기능 표기 금지. 실제화하면 코드 표시를 지우고 목록을 `REAL`로. 같은 항목을 새 번호로 다시 등록하지 않습니다.
14. **결함**: 제품 결함은 `worklog/DEFECTS.md`에 `DEF-YYYYMMDD-NN`(`new-id DEF`) 한 줄. Task는 번호로만 참조합니다(`defects_found:`, `fixes:`). P0는 바로 담당 Task를 정해 `fixing`.
15. **git 상태**: 잠금 영역 밖의 미커밋 변경은 남의 것일 수 있으니 건드리지 말고 주인·사용자에게 확인합니다. 배포는 **원격에 있는 SHA로만**: push(사용자 승인) 뒤 배포하고 `■ 종료 [DEPLOY] … 배포 SHA = <sha>`를 적습니다.
16. **전달 등급**: 채팅 전달은 **알림(L0)** 일 뿐 기록이 아닙니다. 사용자에게 하는 보고는 서명급이 아니어도 **보고서 파일(L1)을 먼저** 쓰고(레포 일은 Task 파일, 본부 일은 공통 구역 `REPORT-YYYYMMDD-HHmm-AG_<slug>.md`) 채팅 끝에 그 경로를 적습니다. 에이전트 간 합의·서명은 **TURN 파일(L2)** 에서만 유효합니다. 채팅으로 전달받은 다른 에이전트의 요약·서명은 원본 파일과 대조하기 전에는 쓰지 않습니다(숫자는 원문 그대로). 문서와 목록은 지우고 다시 쓰지 않고 덧붙여 `정정:`으로 고칩니다. 남이 잠근 브랜치에는 커밋하지 않습니다. "100%·완벽·해결됨"에는 같은 줄에 근거를 붙입니다.
17. **실측 범위**: "실측"에는 실행한 명령을 붙이고 **레포**인지 **운영**인지 구분합니다. 배포 경로·워커·예약 실행·라우트는 레포 파일만 보고 단정하지 않습니다. 레포 안 배포 설정 전체 → 배포 스크립트 → CI·자동 빌드 경로 → 운영 쪽 현재 상태 순으로 보고, 운영을 못 봤으면 "미확인"으로 적습니다. 배포·인프라를 다룬 Task 워크스루에는 `운영 확인: <읽기 전용 명령/화면> → <결과>` 또는 `운영 미확인: <이유>` 줄을 씁니다.
18. **공유 구역**: 턴·플랜·워크스루는 레포 `.agentshare/`(gitignore)에 `agentkit.py share new|import`로 번호를 붙여 둡니다. 시작할 때 `context`의 공유 구역 현재 상태(마지막 작성자·다음 턴)를 봅니다. 에이전트 전용 저장소의 문서는 턴을 끝내기 전에 `share import`로 가져오고, 채팅으로 붙여 넣어 전달하지 않습니다. 결론·검증은 Task §5에 옮기고 `share: #번호`를 적습니다. 공유 구역에도 보안값 금지.

### worklog 양식 (요약, 전체는 원본 `templates/`)
- `NOW.md`: 갱신 시각·갱신자 / 🔒 작업 중 에이전트 표(에이전트 · Task ID · 모드 · 브랜치 · 영역 · 시작) / 🟡 진행 중 / 🔴 막힘 / ⏭️ 다음 할 일 / ✅ 최근 완료 3건 / ⚠️ 알아야 할 것
- `INDEX.md`: `상태 | Task ID(링크) | 시작 | 에이전트 | 우선순위 | 작업 키 | 제목 | 평가`, 최신이 위
- `BADCASES.md`: `일시 | Task ID | 에이전트 | 유형 | 한 줄 교훈`, 최신이 위
- `IMPLEMENTATION.md`: `번호 | 상태 | 기능 | 위치 | 화면 표시 | 실제화 조건 | 만든 Task | 실제화 Task` · `DEFECTS.md`: `번호 | 심각도 | 상태 | 한 줄 설명 | 발견 Task | 수정 Task`
- 작업 파일 머리말(**파일 첫 줄부터 `---` ~ `---`**, 코드펜스 금지): `id, title, status, agent, repo, work, continues, mode, deploy, priority, plan, eval, branch, started, updated, commits, impl, implements, defects_found, fixes, related, escalate` / 섹션: 1 목표 · 2 계획(사전 분석) · 3 체크리스트(WBS 표) · 4 진행 로그(모드 마크) · 5 워크스루(테스트 결과·사후 분석) · 6 인수인계 · 7 사고 기록 · 8 평가
<!-- /anti-gc-sync-pub v1.2.2 -->
