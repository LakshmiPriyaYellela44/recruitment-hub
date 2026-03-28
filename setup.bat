@echo off
REM Color codes
setlocal enabledelayedexpansion

echo ========================================
echo Recruitment Platform - Setup Script
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed. Please install Python 3.11+ first.
    exit /b 1
)

REM Check if Node is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo Node.js is not installed. Please install Node.js 18+ first.
    exit /b 1
)

REM Backend Setup
echo Setting up Backend...
cd backend

REM Create virtual environment
if not exist "venv" (
    python -m venv venv
    echo + Virtual environment created
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install dependencies
pip install -r requirements.txt
echo + Backend dependencies installed

REM Create .env file if it doesn't exist
if not exist ".env" (
    copy .env.example .env
    echo + .env file created (please update DATABASE_URL)
)

cd ..

REM Frontend Setup
echo.
echo Setting up Frontend...
cd frontend

REM Install dependencies
call npm install
echo + Frontend dependencies installed

cd ..

echo.
echo ========================================
echo + Setup completed!
echo ========================================
echo.

echo Next steps:
echo 1. Configure Database:
echo    - Update DATABASE_URL in backend\.env
echo    - Create PostgreSQL database (see README.md)
echo.
echo 2. Start Backend:
echo    cd backend
echo    venv\Scripts\activate.bat
echo    python -m uvicorn app.main:app --reload
echo.
echo 3. Start Frontend (in another terminal):
echo    cd frontend
echo    npm run dev
echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
