# anti-gc-sync-pub

**멀티에이전트(Claude · Antigravity) 공통 작업 계약과 양식** — 공개 규격 저장소 (MIT)

한 레포 안에서 여러 AI 코딩 에이전트가 **같은 기록 파일(`worklog/`)로 서로 소통하며 동시에 작업**할 수 있게 하는 규칙입니다.
에이전트 전용 메모리(세션마다 사라지는 계획서·워크스루)에 의존하지 않고, 레포 안에 남는 일반 Markdown으로 맥락을 이어갑니다.

> 이 저장소에는 시크릿, 계정 정보, 개인 경로가 들어 있지 않습니다. 경로는 `<REPOS_ROOT>` 같은 자리표시자로 적습니다.

## 구성

| 파일 | 내용 |
|---|---|
| [CONTRACT.md](CONTRACT.md) | 공통 계약 본문 (원본) |
| [global/CLAUDE_GLOBAL.md](global/CLAUDE_GLOBAL.md) | Claude 전역 규칙에 설치할 요약본 |
| [global/GEMINI_GLOBAL.md](global/GEMINI_GLOBAL.md) | Antigravity(Gemini) 전역 규칙에 설치할 요약본 |
| [templates/](templates/) | 레포 `worklog/` 양식: NOW, INDEX, BADCASES, TASK |
| [CHANGELOG.md](CHANGELOG.md) | 버전 기록 |

> **현재 확정본: 태그 `v1.0`** · `main`은 v1.1-rc(검토 중): 중복 방지(§3-1), 컨텍스트 운용(§13), P0·확정 플랜·배드 케이스 평가(§14), 자원(§15)

## 왜 컨텍스트 효율 도구인가

`worklog/`는 타임라인·인덱스·목차로 정리되어 있어서, 에이전트가 전체 기록 대신 **필요한 조각만** 불러옵니다. 불필요한 컨텍스트는 추론 오류만 늘리므로, 세션은 항상 작은 "컨텍스트 팩"(NOW + 최근 INDEX + 진행 중 Task 요약 + 최근 배드 케이스)으로 시작합니다.

## 3단 구성

```
① 원본       이 저장소 (버전 태그로 고정: v1.0 …)
② 글로벌 룰   각 PC의 에이전트 전역 규칙 파일에 요약본 설치 → 어느 레포를 열든 자동 적용
③ 레포 룰    각 레포의 AGENTS.md (그 레포만의 규칙)
```

- 레포에 규칙 블록을 복사해 넣지 않습니다. 레포에는 **작업 기록(`worklog/`)만** 생깁니다.
- 규칙이 충돌하면 **더 엄격한 쪽**을 따릅니다.

## 설치 (요약)

1. `global/*_GLOBAL.md`의 `<REPOS_ROOT>`를 내 레포 루트 경로로 바꿉니다.
2. Claude는 `~/.claude/CLAUDE.md`에, Antigravity는 `~/.gemini/GEMINI.md`에 내용을 붙입니다.
3. 첫 줄의 버전 표시(`anti-gc-sync-pub vX.Y`)가 이 저장소의 태그와 같은지 확인합니다.

## 라이선스

MIT — [LICENSE](LICENSE)
