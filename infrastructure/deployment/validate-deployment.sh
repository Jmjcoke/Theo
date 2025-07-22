#!/bin/bash
# Deployment Validation Script for Theo
# This script validates that the deployment is working correctly

set -e

DOMAIN=${1:-localhost}
BACKEND_URL="https://$DOMAIN/health"
FRONTEND_URL="https://$DOMAIN"

echo "🔍 Validating Theo deployment on $DOMAIN..."

# Function to check HTTP status
check_http_status() {
    local url=$1
    local expected_status=${2:-200}
    local description=$3
    
    echo -n "Checking $description... "
    
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" --max-time 30 --connect-timeout 10 || echo "000")
    
    if [ "$status" = "$expected_status" ]; then
        echo "✅ OK (HTTP $status)"
        return 0
    else
        echo "❌ FAILED (HTTP $status)"
        return 1
    fi
}

# Function to check JSON response
check_json_response() {
    local url=$1
    local expected_key=$2
    local expected_value=$3
    local description=$4
    
    echo -n "Checking $description... "
    
    response=$(curl -s "$url" --max-time 30 --connect-timeout 10 || echo "{}")
    value=$(echo "$response" | jq -r ".$expected_key" 2>/dev/null || echo "null")
    
    if [ "$value" = "$expected_value" ]; then
        echo "✅ OK ($expected_key: $value)"
        return 0
    else
        echo "❌ FAILED ($expected_key: $value, expected: $expected_value)"
        echo "Full response: $response"
        return 1
    fi
}

# Function to check content contains text
check_content_contains() {
    local url=$1
    local expected_text=$2
    local description=$3
    
    echo -n "Checking $description... "
    
    content=$(curl -s "$url" --max-time 30 --connect-timeout 10 || echo "")
    
    if echo "$content" | grep -q "$expected_text"; then
        echo "✅ OK (contains: $expected_text)"
        return 0
    else
        echo "❌ FAILED (missing: $expected_text)"
        echo "Content preview: $(echo "$content" | head -c 200)..."
        return 1
    fi
}

# Start validation
validation_passed=true

echo ""
echo "📋 Running deployment validation checks..."
echo "================================="

# Check backend health endpoint
if ! check_http_status "$BACKEND_URL" "200" "backend health endpoint accessibility"; then
    validation_passed=false
fi

# Check backend health JSON response
if ! check_json_response "$BACKEND_URL" "status" "ok" "backend health status JSON"; then
    validation_passed=false
fi

# Check frontend accessibility
if ! check_http_status "$FRONTEND_URL" "200" "frontend accessibility"; then
    validation_passed=false
fi

# Check frontend welcome message
if ! check_content_contains "$FRONTEND_URL" "Welcome to Theo" "frontend welcome message"; then
    validation_passed=false
fi

echo ""
echo "🔒 SSL and Security Checks..."
echo "========================"

# Check HTTPS redirect (if using HTTP)
if [[ $DOMAIN != "localhost" ]]; then
    HTTP_URL="http://$DOMAIN"
    if ! check_http_status "$HTTP_URL" "301" "HTTPS redirect"; then
        validation_passed=false
    fi
    
    # Check SSL certificate
    echo -n "Checking SSL certificate... "
    if openssl s_client -connect "$DOMAIN:443" -servername "$DOMAIN" </dev/null 2>/dev/null | openssl x509 -noout -dates > /dev/null 2>&1; then
        echo "✅ OK"
    else
        echo "❌ FAILED"
        validation_passed=false
    fi
fi

echo ""
echo "🐳 Docker Container Checks..."
echo "=========================="

# Check if containers are running (only works when run on the server)
if command -v docker >/dev/null 2>&1; then
    echo -n "Checking backend container status... "
    if docker ps --filter "name=theo-backend" --filter "status=running" | grep -q theo-backend; then
        echo "✅ Running"
    else
        echo "❌ Not running"
        validation_passed=false
    fi
    
    echo -n "Checking frontend container status... "
    if docker ps --filter "name=theo-frontend" --filter "status=running" | grep -q theo-frontend; then
        echo "✅ Running"
    else
        echo "❌ Not running"
        validation_passed=false
    fi
    
    # Check container health
    echo -n "Checking backend container health... "
    backend_health=$(docker inspect theo-backend --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
    if [ "$backend_health" = "healthy" ]; then
        echo "✅ Healthy"
    else
        echo "❌ $backend_health"
        validation_passed=false
    fi
    
    echo -n "Checking frontend container health... "
    frontend_health=$(docker inspect theo-frontend --format='{{.State.Health.Status}}' 2>/dev/null || echo "unknown")
    if [ "$frontend_health" = "healthy" ]; then
        echo "✅ Healthy"
    else
        echo "❌ $frontend_health"
        validation_passed=false
    fi
else
    echo "⚠️  Docker not available - skipping container checks"
fi

echo ""
echo "📊 Performance Checks..."
echo "===================="

# Check response times
echo -n "Checking backend response time... "
backend_time=$(curl -o /dev/null -s -w '%{time_total}' "$BACKEND_URL" --max-time 30 || echo "timeout")
if [[ "$backend_time" != "timeout" ]] && (( $(echo "$backend_time < 2.0" | bc -l 2>/dev/null || echo "0") )); then
    echo "✅ ${backend_time}s"
else
    echo "⚠️  ${backend_time}s (slow or timeout)"
fi

echo -n "Checking frontend response time... "
frontend_time=$(curl -o /dev/null -s -w '%{time_total}' "$FRONTEND_URL" --max-time 30 || echo "timeout")
if [[ "$frontend_time" != "timeout" ]] && (( $(echo "$frontend_time < 3.0" | bc -l 2>/dev/null || echo "0") )); then
    echo "✅ ${frontend_time}s"
else
    echo "⚠️  ${frontend_time}s (slow or timeout)"
fi

echo ""
echo "================================="

# Final result
if [ "$validation_passed" = true ]; then
    echo "🎉 All validation checks PASSED!"
    echo ""
    echo "Deployment URLs:"
    echo "- Frontend: $FRONTEND_URL"
    echo "- Backend Health: $BACKEND_URL"
    echo "- API Docs: https://$DOMAIN/api/docs"
    echo ""
    exit 0
else
    echo "💥 Some validation checks FAILED!"
    echo ""
    echo "Please check the errors above and:"
    echo "1. Review container logs: docker-compose logs"
    echo "2. Check server resources: htop, df -h"
    echo "3. Verify network connectivity"
    echo "4. Check firewall settings"
    echo ""
    exit 1
fi