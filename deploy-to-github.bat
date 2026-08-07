@echo off
REM Traveling Star Deployment Script
REM This script copies the updated frontend files and commits them to GitHub

echo 🚀 Starting Traveling Star Deployment...

REM Configuration
set SOURCE_PATH=C:\Users\User\LocalDev\traveling-star-frontend\dist
set TARGET_PATH=C:\Users\User\LocalDev\travelingstar-backend\travelingstarservice-pages\public
set PUBLIC_ASSETS=C:\Users\User\LocalDev\traveling-star-frontend\public
set GIT_REPO=C:\Users\User\LocalDev\travelingstar-backend\travelingstarservice-pages

REM Check if source exists
if not exist "%SOURCE_PATH%" (
    echo ❌ Error: Source build directory not found
    echo Please run 'npm run build' in the frontend directory first.
    pause
    exit /b 1
)

REM Copy updated frontend files
echo 📦 Copying updated frontend files...
xcopy "%SOURCE_PATH%\*" "%TARGET_PATH%\" /E /Y /I
xcopy "%PUBLIC_ASSETS%\*" "%TARGET_PATH%\" /E /Y /I

echo ✅ Files copied successfully

REM Navigate to git repository
cd /d "%GIT_REPO%"

REM Check if git is available
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Error: Git is not installed or not in PATH
    echo Please install Git from https://git-scm.com/
    pause
    exit /b 1
)

echo 🔧 Git found

REM Add files to git
echo 📝 Adding files to git...
git add public/

REM Commit changes
echo 💾 Committing changes...
git commit -m "Deploy updated frontend with new features: search bar, upgraded logo, mobile booking, real-time updates"

REM Push to GitHub
echo 🚀 Pushing to GitHub...
git push origin main

echo ✅ Deployment complete!
echo 🌐 Your site will be updated at: https://travelingstarservice.github.io
echo ⏱️ GitHub Actions will build and deploy automatically
pause