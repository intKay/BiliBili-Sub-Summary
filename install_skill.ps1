param(
    [string]$InstallRoot = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    if ([string]::IsNullOrWhiteSpace($env:CODEX_HOME)) {
        $InstallRoot = Join-Path $HOME ".codex\skills"
    } else {
        $InstallRoot = Join-Path $env:CODEX_HOME "skills"
    }
}

$SkillName = "bilibili-video-analysis"
$Target = Join-Path $InstallRoot $SkillName
$BundleScripts = Join-Path $Target "scripts"

New-Item -ItemType Directory -Force -Path $Target | Out-Null
New-Item -ItemType Directory -Force -Path $BundleScripts | Out-Null

Copy-Item -LiteralPath (Join-Path $RepoRoot "skills\$SkillName\SKILL.md") -Destination $Target -Force
Copy-Item -LiteralPath (Join-Path $RepoRoot "skills\$SkillName\PORTABLE_AGENT_PROMPT.md") -Destination $Target -Force
Copy-Item -LiteralPath (Join-Path $RepoRoot "requirements.txt") -Destination $Target -Force
Copy-Item -LiteralPath (Join-Path $RepoRoot "scripts\*.py") -Destination $BundleScripts -Force

Write-Host "Installed $SkillName to $Target"
Write-Host "For Python helpers, create a venv and install dependencies from: $(Join-Path $Target 'requirements.txt')"
