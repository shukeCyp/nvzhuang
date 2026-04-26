@echo off
setlocal

call python -m pip install --upgrade pip
if errorlevel 1 exit /b %errorlevel%

call pip install -r requirements.txt pyinstaller
if errorlevel 1 exit /b %errorlevel%

pushd frontend
call npm ci
if errorlevel 1 (
  popd
  exit /b %errorlevel%
)

call npm run build
if errorlevel 1 (
  popd
  exit /b %errorlevel%
)
popd

if exist "backend\vue" rmdir /s /q "backend\vue"
mkdir "backend\vue"
xcopy "frontend\dist\*" "backend\vue\" /e /i /y >nul
if errorlevel 1 exit /b %errorlevel%

set "PLAYWRIGHT_BROWSERS_PATH=%CD%\ms-playwright"

call python -m playwright install chromium
if errorlevel 1 exit /b %errorlevel%

set "SPEC_FILE="
for %%F in (*.spec) do if not defined SPEC_FILE set "SPEC_FILE=%%~fF"

if not defined SPEC_FILE (
  echo [ERROR] No .spec file found in %CD%
  exit /b 1
)

call pyinstaller --noconfirm "%SPEC_FILE%"
if errorlevel 1 exit /b %errorlevel%

echo.
echo Build complete: dist\女装助手.exe
exit /b 0
