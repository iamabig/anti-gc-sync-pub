#Requires -Version 7.0
# PowerShell 7(pwsh)로 실행하세요. Windows PowerShell 5.1(powershell.exe)은 지원하지 않습니다.
<#
.SYNOPSIS
  AGS-KIT(검수 키) 설치·갱신 — 레포 하나 (사용자가 실행)

.DESCRIPTION
  공개 저장소(anti-gc-sync-pub)를 내려받은 폴더의 kit\install 에서 실행합니다.
  하는 일 (모두 그 레포 안에서만, 커밋·push는 하지 않음):
    1. .agentkit\agentkit.py 복사 (줄바꿈 LF로 고정, 기존 버전 → 새 버전 표시)
    2. AGS-CI: .github\workflows\agent-contract.yml (고정 태그 + 해시. 기본: 🔴면 실패)
    3. .gitignore 에 worklog/.agentkit-report.json, .wt/, .agentshare/ 추가 (없을 때만)
    4. commit-msg 훅 설치 (v1.1 agentkit pre-commit 훅은 지움. 다른 훅이 있으면 덮어쓰지 않고 알림)
    5. worklog 양식: 없는 파일만 만듦 (v1.1 레포는 IMPLEMENTATION.md, DEFECTS.md가 추가됨)
    6. 공유 구역 .agentshare/ (gitignore, v1.2.2) 와 목차 INDEX.md
    7. 마지막에 agentkit.py doctor 로 설치 상태 점검

.EXAMPLE
  .\install_agentkit.ps1 -Repo <레포경로>
.EXAMPLE
  .\install_agentkit.ps1 -Repo <레포경로> -WhatIf       # 바꿀 내용만 보여 주고 아무것도 안 씀
.EXAMPLE
  .\install_agentkit.ps1 -Repo <레포경로> -CIWarnOnly   # CI를 경고만 하게
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [Parameter(Mandatory = $true)][string]$Repo,
  [string]$Ref,                 # AGS-SPEC 태그. 비우면 키에 적힌 규격 버전 (예: v1.2)
  [switch]$NoCI,
  [switch]$CIWarnOnly,
  [switch]$NoHook,
  [switch]$Init                 # (호환용) worklog가 없을 때 양식 생성
)
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$Kit = Split-Path -Parent $PSScriptRoot          # ...\kit
$Src = Join-Path $Kit 'agentkit.py'
$Utf8 = New-Object Text.UTF8Encoding($false)

function Say($icon, $msg) { Write-Host "$icon $msg" }
function LfText($path) { ([IO.File]::ReadAllText($path, $Utf8)) -replace "`r`n", "`n" }
function Sha256Text($text) {
  $sha = [Security.Cryptography.SHA256]::Create()
  ($sha.ComputeHash($Utf8.GetBytes($text)) | ForEach-Object { $_.ToString('x2') }) -join ''
}

# 0. 확인
$Repo = (Resolve-Path $Repo).Path
if (-not (Test-Path (Join-Path $Repo '.git'))) { throw "git 레포가 아닙니다: $Repo" }
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) { $py = Get-Command py -ErrorAction SilentlyContinue }
if (-not $py) { throw "Python이 없습니다. Python 3.9 이상을 설치하세요." }
$verLine = (& $py.Source -I $Src version)
$newVer = $verLine -replace '^agentkit\s+(\S+).*$', '$1'
if (-not $Ref) { $Ref = $verLine -replace '^.*anti-gc-sync-pub\s+(v[\d.]+).*$', '$1' }
$kitText = LfText $Src
$kitSha = Sha256Text $kitText
Say '🔑' "AGS-KIT $newVer (태그 $Ref, sha256 $($kitSha.Substring(0,12))…) → $Repo"

# 1. 키 복사 (LF)
$dstDir = Join-Path $Repo '.agentkit'; $dst = Join-Path $dstDir 'agentkit.py'
$oldVer = if (Test-Path $dst) { (& $py.Source -I $dst version) -replace '^agentkit\s+(\S+).*$', '$1' } else { '없음' }
if ($PSCmdlet.ShouldProcess($dst, "agentkit.py 복사 ($oldVer → $newVer)")) {
  New-Item -ItemType Directory -Force $dstDir | Out-Null
  [IO.File]::WriteAllText($dst, $kitText, $Utf8)
  Say '✅' "키: $oldVer → $newVer"
}

# 2. AGS-CI
if (-not $NoCI) {
  $wfDir = Join-Path $Repo '.github\workflows'; $wf = Join-Path $wfDir 'agent-contract.yml'
  $yml = (LfText (Join-Path $Kit 'ci\agent-contract.yml')) -replace '__AGS_KIT_REF__', $Ref -replace '__AGS_KIT_SHA256__', $kitSha
  if ($CIWarnOnly) { $yml = $yml -replace 'continue-on-error: false', 'continue-on-error: true' }
  if ($PSCmdlet.ShouldProcess($wf, "AGS-CI 설치 (AGS_KIT_REF=$Ref)")) {
    New-Item -ItemType Directory -Force $wfDir | Out-Null
    [IO.File]::WriteAllText($wf, $yml, $Utf8)
    Say '✅' ("AGS-CI: $Ref 고정 · " + ($(if ($CIWarnOnly) { '경고만' } else { '필수 검사 (🔴면 실패)' })))
  }
}

# 3. .gitignore
$gi = Join-Path $Repo '.gitignore'
$cur = if (Test-Path $gi) { Get-Content $gi } else { @() }
foreach ($line in @('worklog/.agentkit-report.json', '.wt/', '.agentshare/')) {
  if ($cur -notcontains $line -and $PSCmdlet.ShouldProcess($gi, "추가: $line")) {
    Add-Content -Path $gi -Value $line -Encoding utf8NoBOM; Say '✅' ".gitignore += $line"
  }
}

# 4. 훅
if (-not $NoHook) {
  $hooksRel = (& git -C $Repo rev-parse --git-path hooks).Trim()
  $hooks = if ([IO.Path]::IsPathRooted($hooksRel)) { $hooksRel } else { Join-Path $Repo $hooksRel }
  $old = Join-Path $hooks 'pre-commit'      # v1.1 훅: 커밋 메시지를 못 봐서 C23을 잘못 막음 → 우리 것이면 지움
  if ((Test-Path $old) -and ((Get-Content $old -Raw) -match 'agentkit') -and $PSCmdlet.ShouldProcess($old, 'v1.1 agentkit pre-commit 훅 제거')) {
    Remove-Item $old -Force; Say '✅' '훅: v1.1 pre-commit 제거 (commit-msg로 바뀜)'
  }
  $hook = Join-Path $hooks 'commit-msg'
  if ((Test-Path $hook) -and -not ((Get-Content $hook -Raw) -match 'agentkit')) {
    Say '⚠️' "다른 commit-msg 훅이 있어 덮어쓰지 않았습니다: $hook (직접 합쳐 주세요)"
  } elseif ($PSCmdlet.ShouldProcess($hook, 'commit-msg 훅 설치')) {
    New-Item -ItemType Directory -Force $hooks | Out-Null
    [IO.File]::WriteAllText($hook, (LfText (Join-Path $Kit 'hooks\commit-msg')), $Utf8)
    Say '✅' '훅: commit-msg (🔴면 커밋 차단)'
  }
}

# 5. worklog 양식 (없는 파일만)
$hasWl = Test-Path (Join-Path $Repo 'worklog')
if (($hasWl -or $Init) -and $PSCmdlet.ShouldProcess("$Repo\worklog", '없는 양식만 생성 (IMPLEMENTATION.md, DEFECTS.md 등)')) {
  Push-Location $Repo; try { & $py.Source -I $dst init --who US } finally { Pop-Location }
}

# 6. 공유 구역 (v1.2.2, gitignore)
$share = Join-Path $Repo '.agentshare'
if (-not (Test-Path $share) -and $PSCmdlet.ShouldProcess($share, '공유 구역 만들기 (gitignore, 목차 INDEX.md)')) {
  Push-Location $Repo; try { & $py.Source -I $dst share index | Out-Null } finally { Pop-Location }
  Say '✅' '공유 구역: .agentshare/ (이 PC에만, git에 안 올라감)'
}

# 7. 점검
if (-not $WhatIfPreference) {
  Write-Host ''
  Push-Location $Repo; try { & $py.Source -I $dst doctor } finally { Pop-Location }
  Write-Host ''
  Say '➡️' "다음: 그 레포 창의 에이전트가 [TaskID] AGS-KIT $newVer 설치 로 커밋합니다 (push는 사용자 승인 후)."
  Say 'ℹ️' "v1.1에서 올렸다면 NOW.md 잠금 표에 '모드' 열을 추가하세요 (doctor 🟡)."
}
