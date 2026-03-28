#!/bin/bash

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Recruitment Platform - Setup Script${NC}"
echo -e "${BLUE}========================================${NC}\n"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed. Please install Python 3.11+ first."
    exit 1
fi

# Check if Node is installed
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Backend Setup
echo -e "${BLUE}Setting up Backend...${NC}"
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
echo -e "${GREEN}✓ Backend dependencies installed${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created (please update DATABASE_URL)${NC}"
fi

cd ..

# Frontend Setup
echo -e "\n${BLUE}Setting up Frontend...${NC}"
cd frontend

# Install dependencies
npm install
echo -e "${GREEN}✓ Frontend dependencies installed${NC}"

cd ..

echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Setup completed!${NC}"
echo -e "${BLUE}========================================${NC}\n"

echo -e "Next steps:"
echo -e "1. ${BLUE}Configure Database:${NC}"
echo -e "   - Update DATABASE_URL in backend/.env"
echo -e "   - Create PostgreSQL database:"
echo -e "     psql -U postgres"
echo -e "     CREATE USER recruitment_user WITH PASSWORD 'recruitment_pass';"
echo -e "     CREATE DATABASE recruitment_db OWNER recruitment_user;"
echo -e ""
echo -e "2. ${BLUE}Start Backend:${NC}"
echo -e "   cd backend"
echo -e "   source venv/bin/activate"
echo -e "   python -m uvicorn app.main:app --reload"
echo -e ""
echo -e "3. ${BLUE}Start Frontend (in another terminal):${NC}"
echo -e "   cd frontend"
echo -e "   npm run dev"
echo -e ""
echo -e "Backend: http://localhost:8000"
echo -e "Frontend: http://localhost:5173"
echo -e "API Docs: http://localhost:8000/docs"
