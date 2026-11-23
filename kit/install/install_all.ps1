<#
.SYNOPSIS
  AGS-KIT 일괄 설치·갱신 — 등록부(레포 목록 표)에 있는 레포 전부 (사용자가 실행)

.DESCRIPTION
  등록부는 마크다운 표입니다. 머리줄에 '레포 경로'가 들어간 열에 `상대경로`(백틱)를 적습니다.
  '폴더' 열이 있으면 계정(폴더)별로 묶어 보여 주고 -Account로 고를 수 있습니다.
  레포마다 install_agentkit.ps1을 부릅니다. 커밋·push는 하지 않습니다 (각 레포 세션 또는 사용자 승인 후).
  **먼저 -WhatIf로 무엇이 바뀌는지 보고** 실행하세요.

.EXAMPLE
  .\install_all.ps1 -Registry <등록부.md> -ReposRoot <레포 루트> -WhatIf
.EXAMPLE
  .\install_all.ps1 -Registry <등록부.md> -ReposRoot <레포 루트> -Account <계정 폴더>
.EXAMPLE
  .\install_all.ps1 -Registry <등록부.md> -ReposRoot <레포 루트> -Only <레포1>,<레포2>
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
  [Parameter(Mandatory = $true)][string]$Registry,
  [Parameter(Mandatory = $true)][string]$ReposRoot,
  [string[]]$Account,           # '폴더' 열 값으로 거르기
  [string[]]$Only,              # 레포 경로에 이 글자가 들어간 것만
  [switch]$CIWarnOnly,
  [switch]$NoHook
)
$ErrorActionPreference = 'Stop'
try { [Console]::OutputEncoding = [Text.Encoding]::UTF8 } catch {}
$one = Join-Path $PSScriptRoot 'install_agentkit.ps1'

$lines = Get-Content $Registry -Encoding utf8 | Where-Object { $_ -match '^\s*\|' -and $_ -notmatch '^\s*\|[\s\-|:]+\|\s*$' }
if (-not $lines) { throw "등록부에서 표를 찾지 못했습니다: $Registry" }
$head = ($lines[0].Trim().Trim('|') -split '\|') | ForEach-Object { $_.Trim() }
$iPath = [Array]::FindIndex($head, [Predicate[string]] { param($h) $h -match '레포 경로' })
$iAcct = [Array]::FindIndex($head, [Predicate[string]] { param($h) $h -eq '폴더' })
if ($iPath -lt 0) { throw "'레포 경로' 열이 없습니다." }

$targets = foreach ($l in $lines | Select-Object -Skip 1) {
  $c = ($l.Trim().Trim('|') -split '\|') | ForEach-Object { $_.Trim() }
  if ($c.Count -le $iPath -or $c[$iPath] -notmatch '`([^`]+)`') { continue }
  $rel = $Matches[1]
  $acct = if ($iAcct -ge 0) { $c[$iAcct] } else { '' }
  if ($Account -and $Account -notcontains $acct) { continue }
  if ($Only -and -not ($Only | Where-Object { $rel -like "*$_*" })) { continue }
  [pscustomobject]@{ Account = $acct; Rel = $rel; Path = (Join-Path $ReposRoot $rel) }
}
Write-Host "대상 $(@($targets).Count)개 (등록부: $(Split-Path -Leaf $Registry))"
$done = 0; $skip = @(); $fail = @()
foreach ($g in ($targets | Group-Object Account)) {
  Write-Host ''; Write-Host "=== 계정/폴더: $($g.Name) ($($g.Count)) ==="
  foreach ($t in $g.Group) {
    if (-not (Test-Path (Join-Path $t.Path '.git'))) { $skip += $t.Rel; Write-Host "⚪ 건너뜀 (git 레포 아님): $($t.Rel)"; continue }
    Write-Host "--- $($t.Rel)"
    try {
      $p = @{ Repo = $t.Path; CIWarnOnly = $CIWarnOnly; NoHook = $NoHook; WhatIf = $WhatIfPreference }
      & $one @p
      $done++
    } catch { $fail += "$($t.Rel): $($_.Exception.Message)"; Write-Host "🔴 실패: $($_.Exception.Message)" }
  }
}
Write-Host ''
$note = if ($WhatIfPreference) { ' (미리보기, 바뀐 것 없음)' } else { '' }
Write-Host "결과: 처리 $done · 건너뜀 $($skip.Count) · 실패 $($fail.Count)$note"
$fail | ForEach-Object { Write-Host "  🔴 $_" }
if (-not $WhatIfPreference) { Write-Host '➡️ 각 레포 세션이 [TaskID] AGS-KIT 설치 로 커밋합니다. push는 사용자 승인 후.' }
