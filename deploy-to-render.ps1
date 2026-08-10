# Traveling Star Render Deployment Script
# This script deploys the backend application to Render

# Configuration
$gitRepoPath = "C:\Users\User\LocalDev\travelingstar-backend.worktrees\windsurf-powershell-chat-ps1-simple-interactive"

Write-Host "Starting Traveling Star Render Deployment..." -ForegroundColor Green

# Navigate to git repository
Set-Location $gitRepoPath

# Check if git is available
try {
    $gitVersion = & git --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Git found: $gitVersion" -ForegroundColor Cyan
    } else {
        throw "Git not found"
    }
} catch {
    Write-Host "Error: Git is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Git from https://git-scm.com/" -ForegroundColor Yellow
    exit 1
}

# Check current branch
$currentBranch = & git branch --show-current
Write-Host "Current branch: $currentBranch" -ForegroundColor Cyan

# Stage all changes
Write-Host "Staging changes..." -ForegroundColor Cyan
& git add .

# Commit changes
$commitMessage = "Deploy backend to Render: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "Committing changes..." -ForegroundColor Cyan
& git commit -m $commitMessage

# Push to GitHub
Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
& git push origin $currentBranch

Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Render will automatically detect the push and deploy your application." -ForegroundColor Cyan
Write-Host "Monitor deployment at: https://dashboard.render.com/" -ForegroundColor Yellow
Write-Host "Your render.yaml configuration will be used for deployment settings." -ForegroundColor Cyan
