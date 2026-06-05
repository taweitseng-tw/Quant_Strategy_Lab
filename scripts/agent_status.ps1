param(
    [int]$Recent = 12
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Title)
    Write-Host ""
    Write-Host "== $Title =="
}

$root = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $root

Write-Host "Quant Strategy Lab agent status"
Write-Host "Root: $root"
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"

Write-Section "Current Task"
if (Test-Path "docs/agent_queue/current_task.md") {
    Get-Content "docs/agent_queue/current_task.md" -TotalCount 80
} else {
    Write-Host "No current task file found."
}

Write-Section "Latest Agent Report"
if (Test-Path "docs/agent_reports") {
    $latestReport = Get-ChildItem "docs/agent_reports" -File -Filter "*.md" |
        Where-Object { $_.Name -ne "README.md" } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if ($latestReport) {
        Write-Host "$($latestReport.FullName)"
        Write-Host "Modified: $($latestReport.LastWriteTime)"
        Get-Content $latestReport.FullName -TotalCount 80
    } else {
        Write-Host "No agent reports found yet."
    }
} else {
    Write-Host "No docs/agent_reports directory found."
}

Write-Section "Version Control"
if (Test-Path ".git") {
    $branch = git branch --show-current
    Write-Host "Branch: $branch"
    $commit = git log -1 --oneline
    Write-Host "Latest Commit: $commit"
    Write-Host ""
    $status = git status --short
    if ([string]::IsNullOrWhiteSpace($status)) {
        Write-Host "Working tree clean."
    } else {
        Write-Host "Status:"
        $status | Out-String | Write-Host
    }
    $ignoredCount = (git ls-files --others --ignored --exclude-standard | Measure-Object).Count
    Write-Host "Ignored untracked files count: $ignoredCount"
} else {
    Write-Host "No .git directory found. Showing recently modified files instead."
    Get-ChildItem -Recurse -File |
        Where-Object {
            $_.FullName -notmatch "\\.venv\\" -and
            $_.FullName -notmatch "\\.pytest_cache\\" -and
            $_.FullName -notmatch "\\__pycache__\\"
        } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First $Recent FullName, LastWriteTime |
        Format-Table -AutoSize |
        Out-String |
        Write-Host
}

Write-Section "Task Board Snapshot"
if (Test-Path "docs/task_board.md") {
    Select-String -Path "docs/task_board.md" -Pattern "## In Progress|## Next|Task 055|Task 054|Blocked" -Context 0,4 |
        Out-String |
        Write-Host
} else {
    Write-Host "No task board found."
}
