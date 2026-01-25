#!/bin/bash

echo "=== BioLink Agentic Chat Application Test Script ==="
echo ""

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 10

# Test backend health
echo "Testing backend health..."
curl -s http://localhost:3001/health | jq . || echo "Backend health check failed"

# Test frontend
echo "Testing frontend..."
curl -s -I http://localhost:3000 | head -1 || echo "Frontend not responding"

# Test SQL agent with simple queries
echo ""
echo "Testing SQL Agent..."

echo "1. Testing patient count query..."
curl -X POST http://localhost:3001/api/chat/sql-agent \
  -H "Content-Type: application/json" \
  -d '{"message": "How many patients are in the database?"}' \
  --max-time 60 | jq .data.content 2>/dev/null || echo "Query timed out or failed"

echo ""
echo "2. Testing age distribution query (with visualization)..."
curl -X POST http://localhost:3001/api/chat/sql-agent \
  -H "Content-Type: application/json" \
  -d '{"message": "Show me the age distribution of patients"}' \
  --max-time 120 | jq .data.content 2>/dev/null || echo "Query timed out or failed"

echo ""
echo "3. Testing EF values query..."
curl -X POST http://localhost:3001/api/chat/sql-agent \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the average EF values for males vs females?"}' \
  --max-time 120 | jq .data.content 2>/dev/null || echo "Query timed out or failed"

echo ""
echo "=== Test Complete ==="
echo "If queries succeeded, the LangGraph agent is working correctly!"
echo "Open http://localhost:3000 in your browser to test the full chat interface."