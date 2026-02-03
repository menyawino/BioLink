#!/bin/bash

# Quick test wrapper for BioLink
set -e

echo "Running quick tests..."
if [ -f "tests/test_agent.sh" ]; then
  echo "- Running test_agent.sh"
  bash tests/test_agent.sh || { echo "test_agent.sh failed"; exit 1; }
else
  echo "- tests/test_agent.sh not found"
fi

if [ -f "tests/test_queries.sh" ]; then
  echo "- Running test_queries.sh"
  bash tests/test_queries.sh || { echo "test_queries.sh failed"; exit 1; }
else
  echo "- tests/test_queries.sh not found"
fi

echo "Quick tests completed."