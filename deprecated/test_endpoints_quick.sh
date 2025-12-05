#!/bin/bash
# Quick test script for AI Summary API endpoints
# Usage: ./test_endpoints_quick.sh MRG_001

if [ -z "$1" ]; then
    echo "Usage: ./test_endpoints_quick.sh <reference_id>"
    echo "Example: ./test_endpoints_quick.sh MRG_001"
    exit 1
fi

REFERENCE_ID=$1
BASE_URL="http://localhost:5002"

echo "=========================================="
echo "Testing AI Summary API Endpoints"
echo "Reference ID: $REFERENCE_ID"
echo "=========================================="

# Test 1: Get Progress
echo ""
echo "1. GET /merge/$REFERENCE_ID/summary-progress"
echo "------------------------------------------"
curl -s "$BASE_URL/merge/$REFERENCE_ID/summary-progress" | python -m json.tool

# Test 2: Regenerate All (commented out by default)
# echo ""
# echo "2. POST /merge/$REFERENCE_ID/regenerate-summaries"
# echo "------------------------------------------"
# curl -s -X POST "$BASE_URL/merge/$REFERENCE_ID/regenerate-summaries" | python -m json.tool

# Test 3: Regenerate Single (example with change_id=1)
# echo ""
# echo "3. POST /merge/change/1/regenerate-summary"
# echo "------------------------------------------"
# curl -s -X POST "$BASE_URL/merge/change/1/regenerate-summary" | python -m json.tool

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
