<#
.SYNOPSIS
    GRACE Framework bootstrapper (PowerShell / Windows).
.DESCRIPTION
    Pulls the clean framework from GitHub and copies it into a target repository
    without touching the target's .git, README.md or the framework's own bootstrap files.
.PARAMETER Target
    Target directory to install the framework into. Default: current directory.
.PARAMETER Ref
    Branch/tag/commit to pull. Default: main.
.PARAMETER Repo
    Source repository URL. Default: SleepyyyZZZZ/GRACE_FRAMEWORK.
.PARAMETER Force
    Overwrite existing framework files in the target.
.EXAMPLE
    iwr -useb https://raw.githubusercontent.com/SleepyyyZZZZ/GRACE_FRAMEWORK/main/bootstrap.ps1 | iex
.EXAMPLE
    ./bootstrap.ps1 -Target . -Force
#>
[CmdletBinding()]
param(
    [string]$Target = ".",
    [string]$Ref    = "main",
    [string]$Repo   = "https://github.com/SleepyyyZZZZ/GRACE_FRAMEWORK.git",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$excludes = @(".git", "README.md", "bootstrap.sh", "bootstrap.ps1")

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "[GRACE] git is required"; exit 1
}

$null = New-Item -ItemType Directory -Force -Path $Target
$Target = (Resolve-Path $Target).Path
$tmp = Join-Path ([System.IO.Path]::GetTempPath()) ("grace_" + [System.IO.Path]::GetRandomFileName())
$null = New-Item -ItemType Directory -Force -Path $tmp

try {
    Write-Host "[GRACE] Cloning $Repo@$Ref ..."
    $clonePath = Join-Path $tmp "grace"
    & git clone --quiet --depth 1 --branch $Ref $Repo $clonePath 2>$null
    if ($LASTEXITCODE -ne 0) { & git clone --quiet --depth 1 $Repo $clonePath }
    if ($LASTEXITCODE -ne 0) { throw "[GRACE] clone failed" }

    Write-Host "[GRACE] Installing framework into: $Target"
    $srcRoot = (Resolve-Path $clonePath).Path
    $files = Get-ChildItem -Path $srcRoot -Recurse -File -Force |
        Where-Object { $_.FullName -notmatch [regex]::Escape((Join-Path $srcRoot ".git") + [System.IO.Path]::DirectorySeparatorChar) }

    foreach ($f in $files) {
        $rel = $f.FullName.Substring($srcRoot.Length).TrimStart('\', '/')
        $top = ($rel -split '[\\/]')[0]
        if ($excludes -contains $rel -or $excludes -contains $top) { continue }

        $dest = Join-Path $Target $rel
        if (-not $Force -and (Test-Path $dest)) {
            Write-Host "[GRACE] skip (exists): $rel"
            continue
        }
        $destDir = Split-Path -Parent $dest
        if ($destDir -and -not (Test-Path $destDir)) {
            $null = New-Item -ItemType Directory -Force -Path $destDir
        }
        Copy-Item -LiteralPath $f.FullName -Destination $dest -Force
    }

    Write-Host "[GRACE] Done. Open CLAUDE.md / AGENTS.md / GEMINI.md and start working."
    Write-Host "[GRACE] Next: pip install -r requirements.txt; python tools/check_semantics.py"
}
finally {
    Remove-Item -Recurse -Force $tmp -ErrorAction SilentlyContinue
}
