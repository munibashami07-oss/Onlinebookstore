$repoPath = $PSScriptRoot

Set-Location $repoPath

Write-Host "Watching: $repoPath"
Write-Host "Auto GitHub push is ACTIVE."
Write-Host "Save a file in VS Code to trigger a push."
Write-Host ""

$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $repoPath
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

# Watch for files being saved/changed
$watcher.NotifyFilter = [System.IO.NotifyFilters]'LastWrite, FileName, Size'

$action = {

    # Ignore changes inside .git
    if ($Event.SourceEventArgs.FullPath -like "*\.git\*") {
        return
    }

    Start-Sleep -Milliseconds 500

    # Prevent multiple Git operations from running at the same time
    if ($global:gitRunning) {
        return
    }

    $global:gitRunning = $true

    try {
        Set-Location $repoPath

        # Check whether there are actual changes
        $status = git status --porcelain

        if ($status) {

            Write-Host ""
            Write-Host "Change detected!" -ForegroundColor Cyan

            git add .

            $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

            git commit -m "Auto update: $timestamp"

            git push

            Write-Host "Successfully pushed to GitHub!" -ForegroundColor Green
            Write-Host ""
        }
    }
    catch {
        Write-Host "Git push failed:" -ForegroundColor Red
        Write-Host $_
    }
    finally {
        $global:gitRunning = $false
    }
}

Register-ObjectEvent `
    -InputObject $watcher `
    -EventName Changed `
    -Action $action | Out-Null

Register-ObjectEvent `
    -InputObject $watcher `
    -EventName Created `
    -Action $action | Out-Null

Register-ObjectEvent `
    -InputObject $watcher `
    -EventName Renamed `
    -Action $action | Out-Null

while ($true) {
    Start-Sleep -Seconds 1
}