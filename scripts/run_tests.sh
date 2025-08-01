#!/bin/bash

# 🧪 Comprehensive Test Runner for Theo MVP
# Created by Quinn (QA Architect)

set -e

echo "🧪 Starting Comprehensive Test Suite for Theo MVP"
echo "=================================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test results tracking
BACKEND_TESTS_PASSED=0
FRONTEND_TESTS_PASSED=0
TOTAL_TESTS=0

echo ""
echo "🔧 Setting up test environment..."

# Backend Tests
echo ""
echo "🐍 Running Backend Tests (FastAPI + pytest)"
echo "============================================"

cd apps/api

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run backend tests with proper Python path
echo "Running API tests..."
PYTHONPATH=$PWD python -m pytest tests/api/ -v --tb=short

echo "Running node tests..."
PYTHONPATH=$PWD python -m pytest tests/nodes/ -v --tb=short

echo "Running flow tests..."
PYTHONPATH=$PWD python -m pytest tests/flows/ -v --tb=short

echo "Running utility tests..."
PYTHONPATH=$PWD python -m pytest tests/utils/ -v --tb=short

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Backend tests PASSED${NC}"
    BACKEND_TESTS_PASSED=1
else
    echo -e "${RED}❌ Backend tests FAILED${NC}"
fi

# Frontend Tests
echo ""
echo "⚛️  Running Frontend Tests (React + Vitest)"
echo "==========================================="

cd ../../apps/web

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "Installing npm dependencies..."
    npm install
fi

# Run frontend tests
echo "Running component tests..."
npm run test:coverage

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Frontend tests PASSED${NC}"
    FRONTEND_TESTS_PASSED=1
else
    echo -e "${RED}❌ Frontend tests FAILED${NC}"
fi

# Summary
echo ""
echo "📊 Test Results Summary"
echo "======================="

if [ $BACKEND_TESTS_PASSED -eq 1 ] && [ $FRONTEND_TESTS_PASSED -eq 1 ]; then
    echo -e "${GREEN}🎉 ALL TESTS PASSED!${NC}"
    echo "✅ Backend: PASSED"
    echo "✅ Frontend: PASSED"
    echo ""
    echo "🚀 Your MVP is ready for deployment!"
    exit 0
else
    echo -e "${RED}🚨 SOME TESTS FAILED${NC}"
    if [ $BACKEND_TESTS_PASSED -eq 0 ]; then
        echo "❌ Backend: FAILED"
    else
        echo "✅ Backend: PASSED"
    fi
    
    if [ $FRONTEND_TESTS_PASSED -eq 0 ]; then
        echo "❌ Frontend: FAILED"
    else
        echo "✅ Frontend: PASSED"
    fi
    echo ""
    echo "🔧 Please fix failing tests before deployment."
    exit 1
fi