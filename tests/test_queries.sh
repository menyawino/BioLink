#!/bin/bash

echo "=== BioLink SQL Agent Query Tester ==="
echo ""

BASE_URL="http://localhost:3001"

# Test queries
queries=(
    "How many patients are in the database?"
    "What is the average age of patients?"
    "Count patients by gender"
    "Show age distribution by gender"
    "What is the average EF for males?"
)

echo "Testing SQL Agent API..."
echo "========================"

for i in "${!queries[@]}"; do
    echo ""
    echo "Test $((i+1)): ${queries[$i]}"
    echo "----------------------------------------"

    response=$(curl -s -X POST "$BASE_URL/api/chat/sql-agent" \
        -H "Content-Type: application/json" \
        -d "{\"message\": \"${queries[$i]}\"}" \
        --max-time 60)

    if [ $? -eq 0 ] && [ -n "$response" ]; then
        # Extract the content from the response
        content=$(echo "$response" | jq -r '.data.content // .content // "No content field"')
        echo "✓ Success: $(echo "$content" | head -1 | cut -c1-100)..."
    else
        echo "✗ Failed or timed out"
    fi
done

echo ""
echo "========================"
echo "Testing complete!"
echo ""
echo "For more detailed testing, see ../docs/MANUAL_TEST.md"
echo "Open http://localhost:3000 for the web interface"