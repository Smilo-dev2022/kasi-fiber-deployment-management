#!/bin/bash

echo "=== FIBER PON Tracker App Demo ==="
echo ""
echo "Testing API endpoints..."
echo ""

BASE_URL="http://localhost:5000"

echo "1. Testing server health..."
curl -s "$BASE_URL/api/auth/user" | grep -q "No token" && echo "✅ Server is running and authentication is working"

echo ""
echo "2. Testing user registration..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "password123",
    "role": "project_manager",
    "phone": "+1234567890"
  }')

if echo "$RESPONSE" | grep -q "token"; then
  echo "✅ User registration working"
  TOKEN=$(echo "$RESPONSE" | grep -o '"token":"[^"]*"' | cut -d'"' -f4)
  echo "   Generated JWT token: ${TOKEN:0:20}..."
else
  echo "❌ User registration failed (user may already exist)"
fi

echo ""
echo "3. Testing PON creation (requires authentication)..."
if [ ! -z "$TOKEN" ]; then
  PON_RESPONSE=$(curl -s -X POST "$BASE_URL/api/pons" \
    -H "Content-Type: application/json" \
    -H "x-auth-token: $TOKEN" \
    -d '{
      "ponId": "PON-001",
      "name": "Test PON Installation",
      "location": "Cape Town, South Africa",
      "startDate": "2024-01-15",
      "expectedEndDate": "2024-02-15",
      "fiberCount": 24,
      "coordinates": {
        "latitude": -33.9249,
        "longitude": 18.4241
      }
    }')
  
  if echo "$PON_RESPONSE" | grep -q "ponId"; then
    echo "✅ PON creation working"
    echo "   Created PON: $(echo "$PON_RESPONSE" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)"
  else
    echo "❌ PON creation failed"
  fi
else
  echo "⚠️  Skipping PON test (no authentication token)"
fi

echo ""
echo "4. Available API endpoints:"
echo "   🔐 POST /api/auth/register - User registration"
echo "   🔐 POST /api/auth/login - User login"
echo "   📊 GET /api/reports/dashboard - Dashboard statistics"
echo "   🏗️  GET /api/pons - List PONs"
echo "   🏗️  POST /api/pons - Create PON"
echo "   📋 GET /api/tasks - List tasks"
echo "   📋 POST /api/tasks - Create task"
echo "   📸 POST /api/photos/upload/:taskId - Upload evidence"
echo "   📈 GET /api/reports/export/pons - Export PON data"

echo ""
echo "=== Frontend Application ==="
echo "React app can be started with: cd client && npm start"
echo "Access at: http://localhost:3000"
echo ""
echo "=== Production Build ==="
echo "Build with: npm run build"
echo "Serves static files from: client/build/"
echo ""
echo "Demo completed! ✅"