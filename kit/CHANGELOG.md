# AGS-KIT CHANGELOG

| 버전 | 일시 (KST) | 변경 |
|---|---|---|
| 1.2.1 | 2026-11-23 | C29 같은 이름의 배포 설정 중복(wrangler toml·json·jsonc, cron·route 비교), C30 운영 확인·실측 범위(운영 배포·인프라 파일 변경 Task의 `운영 확인:`/`운영 미확인:` 줄, 명령 없는 "실측"). C26 보정: 원격 HEAD가 다른 브랜치를 가리켜도 `main`·`master`는 기본 브랜치, 기본 브랜치의 지난 커밋은 🟡(지금 커밋은 🔴) — 실제 레포 읽기 전용 실행에서 발견 |
| 1.2.0 | 2026-11-23 | 공개 저장소 `kit/`로 이관(태그 고정). C17~C25: 구현 상태(@impl ↔ IMPLEMENTATION), 화면 노출 MOCK, 결함(DEFECTS), 운영 배포 ≥P1, 작업 모드 마크·단독 모드, 주인 없는 미커밋, 🟢 무커밋, 같은 폴더 브랜치 불일치, 원격에 없는 커밋·배포 SHA. 컨텍스트 팩 git 블록 + 열린 결함·남은 구현 상단 배치(AG P2). `new-id IMP|DEF`(AG P3), 에이전트 코드 등록제(`[A-Z]{2}` + 등록 확인), `terms`(TERMS.md 상수 비교), `check --summary`(CI Job Summary), JSON `agentkit-check/2`(open_defects·open_impls·git, AG CQ2). 훅을 `commit-msg`로 교체(메시지의 TaskID를 C23에 반영). AGS-CI 태그 고정·해시 비교. `install_all.ps1`. doctor: 모드 열, CI 고정, `.gitattributes`. **보강**(다른 팀 사례·직접 전달 분석): C26 남의 잠금 브랜치 커밋, C27 목록 Append-Only, C28 근거 없는 단정, `collab` 명령 R1~R8 |
| 1.1.2 | 2026-11-23 | C11에 '같은 TaskID의 worklog만 고친 후속 커밋' 경고 |
| 1.1.1 | 2026-11-23 | Antigravity 실전 검수 반영, `doctor`, 설치 스크립트, pre-commit 훅, CI 필수 검사 |
| 1.1.0 | 2026-11-23 | 최초: init · new-id · context · check(C1~C16) · hash |
