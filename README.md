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
| [templates/](templates/) | 레포 `worklog/` 양식: NOW, INDEX, TASK |
| [CHANGELOG.md](CHANGELOG.md) | 버전 기록 |

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
