#!/bin/bash

echo "=== Quick BioLink Agent Test ==="
echo ""

# Test 1: Backend health
echo "1. Testing backend health..."
if curl -s --max-time 5 http://localhost:3001/health > /dev/null 2>&1; then
    echo "✓ Backend is responding"
else
    echo "✗ Backend not responding - start services first"
    echo "Run: docker-compose up -d"
    exit 1
fi

# Test 2: Simple SQL query
echo ""
echo "2. Testing simple SQL query..."
response=$(curl -s --max-time 30 -X POST http://localhost:3001/api/chat/sql-agent \
  -H "Content-Type: application/json" \
  -d '{"message": "How many patients are in the database?"}')

if [ $? -eq 0 ] && echo "$response" | grep -q "success.*true"; then
    content=$(echo "$response" | grep -o '"content":"[^"]*"' | head -1 | sed 's/"content":"//' | sed 's/"$//')
    echo "✓ Query successful: ${content:0:50}..."
else
    echo "✗ Query failed or timed out"
    echo "Response: $response"
fi

# Test 3: Visualization query
echo ""
echo "3. Testing visualization query..."
response=$(curl -s --max-time 60 -X POST http://localhost:3001/api/chat/sql-agent \
  -H "Content-Type: application/json" \
  -d '{"message": "Show age distribution"}')

if [ $? -eq 0 ] && echo "$response" | grep -q "success.*true"; then
    if echo "$response" | grep -q "data:image"; then
        echo "✓ Visualization query successful with image"
    else
        content=$(echo "$response" | grep -o '"content":"[^"]*"' | head -1 | sed 's/"content":"//' | sed 's/"$//')
        echo "✓ Query successful (no image): ${content:0:50}..."
    fi
else
    echo "✗ Visualization query failed or timed out"
fi

echo ""
echo "=== Test Complete ==="
echo "If tests passed, the agent is working!"
echo "Open http://localhost:3000 for the full chat interface."