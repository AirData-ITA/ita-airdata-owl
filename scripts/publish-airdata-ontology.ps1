param(
    [string]$OwlFile,
    [string]$OntologySiteRepo,
    [switch]$SkipBuild,
    [switch]$SkipSiteRepo,
    [switch]$Commit,
    [switch]$Push,
    [switch]$DeployLessonia,
    [string]$RemoteHost = $(if ($env:LESSONIA_HOST) { $env:LESSONIA_HOST } else { "161.24.29.22" }),
    [string]$RemoteUser = $(if ($env:LESSONIA_USER) { $env:LESSONIA_USER } else { "guilhermetolentino" }),
    [int]$RemotePort = $(if ($env:LESSONIA_PORT) { [int]$env:LESSONIA_PORT } else { 2222 }),
    [string]$RemotePath = $env:LESSONIA_PATH,
    [string]$SshKey = $env:LESSONIA_SSH_KEY,
    [switch]$CleanRemote
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Resolve-Path (Join-Path $ScriptDir "..")
$OntologyDir = Join-Path $ProjectRoot "ontology"
$OutputSiteDir = Join-Path $ProjectRoot "output\site"

if (-not $OntologySiteRepo) {
    $OntologySiteRepo = Join-Path (Split-Path -Parent $ProjectRoot) "ita-airdata-ontology"
}

function Invoke-Step {
    param(
        [string]$Title,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Title" -ForegroundColor Cyan
    & $Command
}

function Invoke-CheckedCommand {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory = $ProjectRoot
    )

    Push-Location $WorkingDirectory
    try {
        & $FilePath @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
        }
    }
    finally {
        Pop-Location
    }
}

function Get-VersionedOntology {
    param([string]$PathOrName)

    if ($PathOrName) {
        $candidate = if ([System.IO.Path]::IsPathRooted($PathOrName)) {
            $PathOrName
        }
        else {
            Join-Path $OntologyDir $PathOrName
        }

        if (-not (Test-Path $candidate)) {
            throw "Ontology file not found: $candidate"
        }

        $file = Get-Item $candidate
        if ($file.Name -notmatch '^airdata_owl_v\d+\.\d+\.\d+\.owl$') {
            throw "Ontology filename must match airdata_owl_vX.Y.Z.owl: $($file.Name)"
        }

        return $file
    }

    $files = Get-ChildItem $OntologyDir -Filter "airdata_owl_v*.owl" | Where-Object {
        $_.Name -match '^airdata_owl_v(?<version>\d+\.\d+\.\d+)\.owl$'
    } | ForEach-Object {
        [pscustomobject]@{
            File = $_
            Version = [version]$Matches.version
        }
    }

    if (-not $files) {
        throw "No versioned ontology found in $OntologyDir"
    }

    return ($files | Sort-Object Version -Descending | Select-Object -First 1).File
}

function Get-GitHasChanges {
    param([string]$RepoPath)

    Push-Location $RepoPath
    try {
        $status = git status --porcelain
        return -not [string]::IsNullOrWhiteSpace(($status -join "`n"))
    }
    finally {
        Pop-Location
    }
}

$SelectedOntology = Get-VersionedOntology $OwlFile
$SelectedOntology.LastWriteTime = Get-Date
$Version = [regex]::Match($SelectedOntology.Name, '^airdata_owl_v(?<version>\d+\.\d+\.\d+)\.owl$').Groups["version"].Value
$CommitMessage = "Update AirData ontology site to v$Version"

Write-Host "AirData ontology publish" -ForegroundColor Green
Write-Host "Project: $ProjectRoot"
Write-Host "Ontology: $($SelectedOntology.FullName)"
Write-Host "Version: v$Version"
Write-Host "Site repo: $OntologySiteRepo"

if (-not $SkipBuild) {
    Invoke-Step "Build generated site" {
        Invoke-CheckedCommand "python" @("make.py", "all") $ProjectRoot
    }
}

if (-not (Test-Path $OutputSiteDir)) {
    throw "Generated site directory not found: $OutputSiteDir"
}

if (-not $SkipSiteRepo) {
    if (-not (Test-Path $OntologySiteRepo)) {
        throw "Ontology site repository not found: $OntologySiteRepo"
    }

    Invoke-Step "Copy output/site to ontology site repository" {
        & robocopy @(
            $OutputSiteDir,
            $OntologySiteRepo,
            "/E",
            "/XD", ".git",
            "/XF", "README.md"
        )

        if ($LASTEXITCODE -gt 7) {
            throw "Robocopy failed with exit code $LASTEXITCODE"
        }

        $global:LASTEXITCODE = 0
    }

    Invoke-Step "Show site repository changes" {
        Invoke-CheckedCommand "git" @("status", "--short") $OntologySiteRepo
    }

    if ($Commit -and (Get-GitHasChanges $OntologySiteRepo)) {
        Invoke-Step "Commit site repository changes" {
            Invoke-CheckedCommand "git" @("add", ".") $OntologySiteRepo
            Invoke-CheckedCommand "git" @("commit", "-m", $CommitMessage) $OntologySiteRepo
        }
    }

    if ($Push) {
        Invoke-Step "Push site repository" {
            Invoke-CheckedCommand "git" @("push") $OntologySiteRepo
        }
    }
}

if ($Commit -and (Get-GitHasChanges $ProjectRoot)) {
    Invoke-Step "Commit source repository changes" {
        Invoke-CheckedCommand "git" @("add", "ontology", "output", "scripts\publish-airdata-ontology.ps1", "AUTOMATION.md") $ProjectRoot
        Invoke-CheckedCommand "git" @("commit", "-m", "Add AirData ontology v$Version") $ProjectRoot
    }
}

if ($Push) {
    Invoke-Step "Push source repository" {
        Invoke-CheckedCommand "git" @("push") $ProjectRoot
    }
}

if ($DeployLessonia) {
    if (-not $RemoteHost -or -not $RemoteUser -or -not $RemotePath) {
        throw "Set RemoteHost, RemoteUser and RemotePath, or define LESSONIA_HOST, LESSONIA_USER and LESSONIA_PATH."
    }

    $Timestamp = Get-Date -Format "yyyyMMddHHmmss"
    $Archive = Join-Path $env:TEMP "airdata-ontology-site-v$Version-$Timestamp.tar.gz"
    $RemoteArchive = "/tmp/airdata-ontology-site-v$Version-$Timestamp.tar.gz"
    $Remote = "${RemoteUser}@${RemoteHost}"

    $SshArgs = @("-p", "$RemotePort")
    $ScpArgs = @("-P", "$RemotePort")
    if ($SshKey) {
        $SshArgs = @("-i", $SshKey) + $SshArgs
        $ScpArgs = @("-i", $SshKey) + $ScpArgs
    }

    Invoke-Step "Create deployment archive" {
        Push-Location $OutputSiteDir
        try {
            Invoke-CheckedCommand "tar" @("-czf", $Archive, ".") $OutputSiteDir
        }
        finally {
            Pop-Location
        }
    }

    Invoke-Step "Upload archive to Lessonia" {
        Invoke-CheckedCommand "scp" ($ScpArgs + @($Archive, "${Remote}:${RemoteArchive}")) $ProjectRoot
    }

    $DeployCommand = if ($CleanRemote) {
        "set -e; test -n '$RemotePath'; rm -rf '$RemotePath'; mkdir -p '$RemotePath'; tar -xzf '$RemoteArchive' -C '$RemotePath'; rm -f '$RemoteArchive'"
    }
    else {
        "set -e; mkdir -p '$RemotePath'; tar -xzf '$RemoteArchive' -C '$RemotePath'; rm -f '$RemoteArchive'"
    }

    Invoke-Step "Extract site on Lessonia" {
        Invoke-CheckedCommand "ssh" ($SshArgs + @($Remote, $DeployCommand)) $ProjectRoot
    }

    Remove-Item -LiteralPath $Archive -Force
}

Write-Host ""
Write-Host "Done. AirData ontology site is ready for v$Version." -ForegroundColor Green
