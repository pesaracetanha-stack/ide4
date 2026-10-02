@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ======================================
echo   Sync to GitHub - ide4
echo ======================================
echo.

git add -A

git diff --cached --quiet
if %errorlevel%==0 (
    echo [i] No changes to commit.
    goto :push
)

for /f "tokens=1-3 delims=/ " %%a in ('date /t') do set d=%%c-%%a-%%b
for /f "tokens=1-2 delims=:." %%a in ('time /t') do set t=%%a:%%b

git commit -m "auto-sync: %d% %t%"

:push
echo.
echo [i] Pushing to GitHub...
git push origin main

echo.
echo ======================================
echo   Done.
echo ======================================
pause