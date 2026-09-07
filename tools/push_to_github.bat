@echo off
title Push Dashboard to GitHub
cd /d "%~dp0\.."

echo ======================================================
echo Staging all changes...
echo ======================================================
git add .

set /p commit_msg="Enter commit message (or press ENTER for default): "
if "%commit_msg%"=="" set commit_msg="Update dashboard content and assets"

echo.
echo ======================================================
echo Committing changes...
echo ======================================================
git commit -m "%commit_msg%"

echo.
echo ======================================================
echo Pushing to GitHub (main branch)...
echo ======================================================
git push origin main

echo.
if %ERRORLEVEL% equ 0 (
    echo ======================================================
    echo SUCCESS! Changes are pushed to GitHub.
    echo Render will now automatically deploy the live site.
    echo ======================================================
) else (
    echo ======================================================
    echo Push encountered an issue. Check the logs above.
    echo ======================================================
)

echo.
pause