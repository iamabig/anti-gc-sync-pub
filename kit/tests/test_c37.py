"""C37 평문 시크릿 시나리오 시험 (AGS-KIT v1.2.4). 가짜 키는 실행 중에 이어 붙여 만들어 이 파일에 진짜 모양이 없게 함.
사용: python -I kit/tests/test_c37.py kit/agentkit.py
"""
import sys, os, subprocess, tempfile, json, base64, shutil

sys.stdout.reconfigure(encoding="utf-8")
KIT = os.path.abspath(sys.argv[1])
ok = fail = 0


def run(cwd, *a):
    return subprocess.run(list(a), cwd=cwd, capture_output=True, text=True, encoding="utf-8")


def check(repo):
    out = os.path.join(repo, "..", "r.json")
    env = dict(os.environ); env.pop("CI", None); env.pop("GITHUB_ACTIONS", None)
    p = subprocess.run([sys.executable, "-I", KIT, "check", "--only", "C37", "--json", out], cwd=repo, capture_output=True, text=True, encoding="utf-8", env=env)
    data = json.load(open(out, encoding="utf-8"))
    c = [x for x in data["results"] if x["id"] == "C37"][0]
    return c, p.stdout


def repo_with(files, gitignore=".env\n.env.*\n!.env.example\n.dev.vars\n"):
    d = tempfile.mkdtemp(prefix="c37-")
    r = os.path.join(d, "r"); os.makedirs(r)
    run(r, "git", "init", "-q"); run(r, "git", "config", "user.email", "t@t"); run(r, "git", "config", "user.name", "t")
    os.makedirs(os.path.join(r, "worklog"))
    open(os.path.join(r, "worklog", "INDEX.md"), "w").write("# INDEX\n")
    if gitignore is not None:
        open(os.path.join(r, ".gitignore"), "w").write(gitignore)
    for name, body in files.items():
        p = os.path.join(r, name); os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "w", encoding="utf-8").write(body)
    run(r, "git", "add", "-A", "-f"); run(r, "git", "commit", "-qm", "init")
    return d, r


def case(name, files, want_level, must=(), must_not=(), gitignore=".env\n.env.*\n!.env.example\n.dev.vars\n"):
    global ok, fail
    d, r = repo_with(files, gitignore)
    try:
        c, out = check(r)
        txt = json.dumps(c, ensure_ascii=False)
        good = c["level"] == want_level and all(m in txt for m in must) and not any(m in txt for m in must_not) and not any(m in out for m in must_not)
    finally:
        shutil.rmtree(d, ignore_errors=True)
    ok += good; fail += not good
    print(("PASS" if good else "FAIL"), name, "→", c["level"], c["msg"][:70])
    if not good:
        for it in c["items"]:
            print("     ", it)


import hashlib
def rnd(n, up=False):
    s = ""; i = 0
    while len(s) < n:
        s += base64.b64encode(hashlib.sha256(f"c37-{i}".encode()).digest()).decode().replace("+", "").replace("/", "").replace("=", ""); i += 1
    s = s[:n]
    return s.upper().replace("0", "Q") if up else s
aws = "AKIA" + "".join(c for c in rnd(40, True) if c.isalnum())[:16]
gh = "ghp_" + rnd(36)
ant = "sk-" + "ant-" + rnd(40)
gsk = "gsk_" + rnd(48)
hook = "https://discord.com/api/" + "webhooks/123456789012/" + rnd(60)
pk = "-----BEGIN " + "RSA PRIVATE KEY-----"
def jwt(role):
    pl = base64.urlsafe_b64encode(json.dumps({"role": role, "iss": "supabase"}).encode()).decode().rstrip("=")
    return "eyJhbGciOiJIUzI1NiJ9." + pl + ".sig_" + "z" * 20

case("1 깨끗한 레포", {"README.md": "hello\n", ".env.example": "API_KEY=\n"}, "pass")
case("2 AWS 키 코드", {"src/a.js": f"const k = '{aws}'\n"}, "fail", must=["AWS", "AKIA…"], must_not=[aws])
case("3 GitHub 토큰", {"x.md": f"token {gh}\n"}, "fail", must=["GitHub"], must_not=[gh])
case("4 Anthropic 키", {"cfg.py": f"KEY='{ant}'\n"}, "fail", must_not=[ant])
case("5 웹훅 주소", {"n.ps1": f"$u='{hook}'\n"}, "fail", must=["웹훅"], must_not=[hook])
case("6 개인 키", {"k.pem.txt": pk + "\n" + rnd(64) + "\n"}, "fail", must=["개인 키"])
case("6b 개인 키 머리 글자만(파싱 코드) 통과", {"pem.ts": 'const h = "' + pk + '";\nconst f = "-----END";\n'}, "pass")
case("6c 자리표시 sk-xxxx·sk-your-key 통과", {"doc.md": "`sk-" + "x" * 27 + "`\nsk-proj-" + "your-api-key-goes-here-1\n"}, "pass")
case("6d 테스트 파일 키 → 🟡", {"src/a.test.ts": f"const k='{ant}'\n"}, "warn", must=["테스트 파일"], must_not=[ant])
case("6e Groq 키 wrangler에 → 🔴", {"wrangler.jsonc": f'{{"vars": {{"GROQ_API_KEY": "{gsk}"}}}}\n'}, "fail", must=["Groq"], must_not=[gsk])
case("6f 서명된 URL 안 AWS 키 ID → 🟡", {"c.json": f'"u": "https://x.s3.amazonaws.com/a.jpg?X-Amz-Credential={aws}%2F2026"\n'}, "warn", must=["서명된 URL"])
case("6g .dev.vars.example 통과", {".dev.vars.example": "API_KEY=\n"}, "pass")
case("7 service_role JWT", {"app.ts": f"const s='{jwt('service_role')}'\n"}, "fail", must=["service_role"])
case("8 anon JWT 통과", {"app.ts": f"const s='{jwt('anon')}'\n"}, "pass")
case("9 .env 올라감", {".env": "X=1\n"}, "fail", must=[".env`"])
case("10 .dev.vars 올라감", {".dev.vars": "X=1\n"}, "fail", must=[".dev.vars"])
case("11 .env.decisions·.env.infra.example 통과", {".env.decisions": "# 결정 기록\nDEC-1 ok\n", ".env.infra.example": "TOKEN=\n"}, "pass")
case("12 wrangler vars 평문 🟡", {"wrangler.toml": '[vars]\nAPI_TOKEN = "abcd1234efgh5678"\n'}, "warn", must=["API_TOKEN", "abcd…"], must_not=["abcd1234efgh5678"])
case("13 wrangler 공개·자리표시 통과", {"wrangler.toml": '[vars]\nPUBLIC_SITE = "x"\nVITE_API_KEY = "abcdefghijk"\nSUPABASE_ANON_KEY = "abcdefghijkl"\nDB_PASSWORD = "<set-me>"\n'}, "pass")
case("14 supabase env() 통과", {"supabase/config.toml": '[auth]\nsecret = "env(JWT_SECRET)"\n'}, "pass")
case("15 vercel.json env 평문 🟡", {"vercel.json": '{"env": {"STRIPE_SECRET": "abcdefgh12345678"}}\n'}, "warn", must=["STRIPE_SECRET"])
case("16 예외 표시", {"src/a.js": f"const k = '{aws}' // ags-allow: 테스트 값\n"}, "pass", must=["1줄"])
case("17 AWS EXAMPLE 키 통과", {"doc.md": "AKIAIOSFODNN7EXAMPLE\n"}, "pass")
case("18 .gitignore에 .env 없음 🟡", {"README.md": "x\n"}, "warn", must=[".gitignore"], gitignore="node_modules/\n")

# 19 remote 주소 토큰 (로컬)
d, r = repo_with({"README.md": "x\n"})
run(r, "git", "remote", "add", "origin", "https://user:" + "tok" + "en123@github.com/a/b.git")
c, out = check(r)
good = c["level"] == "fail" and "remote" in json.dumps(c, ensure_ascii=False) and "token123" not in out
shutil.rmtree(d, ignore_errors=True); ok += good; fail += not good
print(("PASS" if good else "FAIL"), "19 remote 주소 토큰 →", c["level"])

print(f"결과 {ok}/{ok + fail}")
sys.exit(1 if fail else 0)
