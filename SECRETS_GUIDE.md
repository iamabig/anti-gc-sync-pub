# SECRETS_GUIDE — 플랫폼별 시크릿 격리 (AGS v1.2.4, CONTRACT §24)

> 한 줄: **비밀값은 git에 글자 그대로 넣지 않고 플랫폼 금고에.** git에는 이름만 적은 템플릿(`.env.example`)만 올립니다.
> 점검: `agentkit.py check` C37 (커밋 훅·CI). 값은 출력하지 않고 앞 4글자만 보여 줍니다.

## 1. 플랫폼별 표

| 플랫폼 | ❌ 금지 (git에 글자 그대로) | 🟢 금고 | 로컬 개발 파일 (git 제외) |
|---|---|---|---|
| Cloudflare Workers | `wrangler.toml`의 `[vars]`, `wrangler.jsonc`의 `"vars"`에 비밀 | `wrangler secret put <KEY>` (환경별 `--env`) | `.dev.vars` |
| Vercel | `vercel.json`의 `"env"`에 비밀 | `vercel env add <KEY>` 또는 대시보드 Environment Variables | `.env.local` (`vercel env pull`) |
| Supabase | 프론트엔드 코드에 **service_role** 키, `supabase/config.toml`에 글자 그대로 값 | `supabase secrets set KEY=…` (Edge Function), config.toml은 `env(KEY)` 참조 | `.env.local`, `supabase/.env` |
| AWS | 코드의 액세스 키, `serverless.yml` `provider.environment`에 글자 그대로 값 | Secrets Manager 또는 SSM Parameter Store (`${ssm:/path}`) | `~/.aws/credentials` (레포 밖) |
| GitHub Actions | 워크플로 파일에 값 | Settings → Secrets and variables → Actions (`${{ secrets.KEY }}`) | — |
| Git 공통 | `.env`, `.env.production`, remote 주소 안 토큰 (`https://<토큰>@…`) | — | `.env*` gitignore, 템플릿은 `.env.example` |

## 2. 비밀이 아닌 것 (막지 않음)
- 브라우저로 나가는 공개용 값: `NEXT_PUBLIC_*`, `VITE_*`, `PUBLIC_*`, Supabase **anon** 키, 키 제한을 건 Google 브라우저 키. **공개용 접두어에 비밀을 넣지 않습니다.**
- 자리표시 값: `sk-xxxx`, `your-api-key`, `<set-me>`, `env(KEY)`, `${KEY}`
- 공개 키·가짜 테스트 값: 같은 줄에 `# ags-allow: <이유>` (JSON처럼 주석이 안 되는 파일은 값 옆 필드에, 또는 테스트 값을 실행 중에 만들기)

## 3. 이미 올라갔을 때 (순서 고정)
1. **재발급**: 그 서비스에서 새 키를 만들고 옛 키를 폐기합니다. push됐다면 이미 복사됐다고 보고, 지우기 전에 이것부터 합니다.
2. **금고에 새 키**: 위 표의 금고 명령.
3. **파일에서 지움**: 환경 변수 파일은 `git rm --cached <파일>` 뒤 `.gitignore`에 추가. 설정 파일 vars 칸은 이름만 남기거나 지움.
4. **이력**: git 이력에서 지울지(`git filter-repo` 등)는 사용자가 정합니다. 1번이 끝났으면 이력의 옛 키는 쓸모가 없습니다.
- 작업 모드 **SENSITIVE**, 종료에 `후속 영향:` (예: 키 교체됨 → 재배포 필요, 다른 세션의 로컬 `.dev.vars` 갱신 필요).
- 보고서·Task·공유 구역에 키 값을 적지 않습니다. 종류와 파일 이름만.

## 4. `.gitignore` (설치 스크립트가 넣는 줄)
```
.env
.env.*
!.env.example
!.env.*.example
.dev.vars
.dev.vars.*
```
- `!` 예외 줄은 반드시 `.env.*` 아래에 둡니다 (git은 아래 줄이 이김).
- 이름이 `.env`로 시작하지만 비밀이 아닌 파일(결정 기록 등)은 새로 만들면 무시됩니다. 이미 올라간 파일은 그대로 추적되며 C37은 `.env`·`.env.local`·`.env.<환경>` 이름만 봅니다. 새 장부는 `worklog/` 아래 다른 이름을 권장합니다.

## 5. C37이 잡는 것 (요약)
| 단계 | 내용 |
|---|---|
| 🔴 커밋 차단 | AWS `AKIA…`, OpenAI·Anthropic `sk-…`, GitHub `ghp_…`·`github_pat_…`, Slack `xox…`, Stripe `sk_live_…`, Groq `gsk_…`, NVIDIA `nvapi-…`, Hugging Face `hf_…`, Discord·Slack 웹훅 주소, 개인 키 본문, Supabase `service_role` JWT, 올라간 `.env`·`.dev.vars`, remote 주소 토큰(로컬만) |
| 🟡 경고 | 설정 파일의 비밀 이름 칸에 글자 그대로 값, Google API 키, 서명된 URL 안 AWS 키 ID, 테스트 파일 안 키 모양, `.gitignore`에 `.env` 없음 |
