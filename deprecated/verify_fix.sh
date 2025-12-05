#!/bin/bash

echo "=========================================="
echo "Conflict Detection Fix Verification"
echo "=========================================="
echo ""

echo "This script will verify that the B vs C content comparison fix is working."
echo ""

# Check if app is running
echo "1. Checking if app is running on port 5002..."
if lsof -i :5002 > /dev/null 2>&1; then
    echo "   ✓ App is running"
else
    echo "   ✗ App is not running"
    echo "   Please start the app first: python app.py"
    exit 1
fi

echo ""
echo "2. Testing ContentComparator with existing session..."
python test_b_vs_c_comparison.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ Fix verification PASSED"
    echo "=========================================="
    echo ""
    echo "The ContentComparator is working correctly."
    echo "Objects with identical content in B and C will be classified as NO_CONFLICT."
    echo ""
    echo "To test with a new merge session:"
    echo "1. Go to http://localhost:5002/merge"
    echo "2. Upload the V3 packages:"
    echo "   - Base: applicationArtifacts/Three Way Testing Files/V3/Base Package.zip"
    echo "   - Customer: applicationArtifacts/Three Way Testing Files/V3/Customer Version.zip"
    echo "   - New Vendor: applicationArtifacts/Three Way Testing Files/V3/Latest Package.zip"
    echo "3. Check if AS_GSS_FM_AddConsensusVersion is now NO_CONFLICT"
else
    echo ""
    echo "=========================================="
    echo "❌ Fix verification FAILED"
    echo "=========================================="
    exit 1
fi
