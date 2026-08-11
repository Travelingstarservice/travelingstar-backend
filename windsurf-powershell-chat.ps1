# windsuf-chat.ps1
# Arthur's Windsurf Chat Module
# Provides folder opener, logo loader, backend starter, git runner, command runner

param(
    [string]$ProjectRoot = "C:\Users\User\LocalDev\travelingstar-backend",
    [string]$FrontendRoot = "C:\Users\User\LocalDev\travelingstar-frontend",
    [string]$VenvActivate = "C:\Users\User\LocalDev\travelingstar-backend\venv\Scripts\Activate.ps1"
)

function loadLogo {
    Write-Host "✨ Traveling Star Service ✨" -ForegroundColor Yellow
    Write-Host "Backend loaded successfully." -ForegroundColor Cyan
}

function startBackend {
    Write-Host "Starting backend..." -ForegroundColor Green
    try {
        & $VenvActivate
        python "$ProjectRoot\app.py"
    }
    catch {
        Write-Host "Backend failed to start: $_" -ForegroundColor Red
    }
}

Clear-Host
Write-Host "Windsurf Chat Module Loaded" -ForegroundColor Cyan
Write-Host "Type /help for commands" -ForegroundColor Yellow

while ($true) {
    $input = Read-Host -Prompt "You"

    switch -Wildcard ($input) {

        "/help" {
            Write-Host ""
            Write-Host "Commands:" -ForegroundColor Green
            Write-Host "  /open backend     Open backend folder in VS Code"
            Write-Host "  /open frontend    Open frontend folder in VS Code"
            Write-Host "  /logo             Show Traveling Star logo"
            Write-Host "  /backend          Start backend (app.py)"
            Write-Host "  /run <cmd>        Run a shell command"
            Write-Host "  /git <args>       Run git"
            Write-Host "  /exit             Exit chat"
            Write-Host ""
        }

        "/open backend" {
            Write-Host "Opening backend folder..." -ForegroundColor Gray
            code $ProjectRoot
        }

        "/open frontend" {
            Write-Host "Opening frontend folder..." -ForegroundColor Gray
            code $FrontendRoot
        }

        "/logo" {
            loadLogo
        }

        "/backend" {
            startBackend
        }

        { $_ -like "/run *" } {
            $cmd = $input.Substring(5)
            Write-Host "Running: $cmd" -ForegroundColor Gray
            Invoke-Expression $cmd
        }

        { $_ -like "/git *" } {
            $args = $input.Substring(5)
            Write-Host "git $args" -ForegroundColor Gray
            git $args
        }

        "/exit" {
            Write-Host "Exiting Windsurf Chat..." -ForegroundColor Yellow
            break
        }

        default {
            Write-Host "Echo: $input"
        }
    }
}

