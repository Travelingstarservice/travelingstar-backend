# Traveling Star Deployment Script
# This script copies the updated frontend files and commits them to GitHub

# Configuration
$sourcePath = "C:\Users\User\LocalDev\traveling-star-frontend\dist"
$targetPath = "C:\Users\User\LocalDev\travelingstar-backend\travelingstarservice-pages\public"
$publicAssetsPath = "C:\Users\User\LocalDev\traveling-star-frontend\public"
$gitRepoPath = "C:\Users\User\LocalDev\travelingstar-backend\travelingstarservice-pages"

Write-Host "Starting Traveling Star Deployment..." -ForegroundColor Green

# Check if source paths exist
if (-not (Test-Path $sourcePath)) {
    Write-Host "Error: Source build directory not found at $sourcePath" -ForegroundColor Red
    Write-Host "Please run 'npm run build' in the frontend directory first." -ForegroundColor Yellow
    exit 1
}

# Copy updated frontend files
Write-Host "Copying updated frontend files..." -ForegroundColor Cyan
Copy-Item -Path "$sourcePath\*" -Destination $targetPath -Recurse -Force
Copy-Item -Path "$publicAssetsPath\*" -Destination $targetPath -Recurse -Force

Write-Host "Files copied successfully" -ForegroundColor Green

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

# Add files to git
Write-Host "Adding files to git..." -ForegroundColor Cyan
& git add public/

# Commit changes
$commitMessage = "Deploy updated frontend with new features: search bar, upgraded logo, mobile booking, real-time updates"
Write-Host "Committing changes..." -ForegroundColor Cyan
& git commit -m $commitMessage

# Push to GitHub
Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
& git push origin main

Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Your site will be updated at: https://travelingstarservice.github.io" -ForegroundColor Cyan
Write-Host "GitHub Actions will build and deploy automatically" -ForegroundColor Yellow