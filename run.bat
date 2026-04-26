@echo off
setlocal

if not exist ".venv" (
  call uv venv .venv
  if errorlevel 1 exit /b %errorlevel%
)

call ".venv\Scripts\activate.bat"
if errorlevel 1 exit /b %errorlevel%

call uv pip install -r requirements.txt
if errorlevel 1 exit /b %errorlevel%

call python -m playwright install chromium 2>nul

pushd frontend
call npm install
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
xcopy "frontend\dist" "backend\vue\" /e /i /y >nul
if errorlevel 1 exit /b %errorlevel%

call python backend\main.py
exit /b %errorlevel%
