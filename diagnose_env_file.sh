#!/bin/bash
echo "=== Diagnosing .env File Issue ==="
echo ""
echo "Checking line 39 of .env file:"
sed -n '39p' .env 2>/dev/null || sed -n '39p' backend/.env 2>/dev/null
echo ""
echo "Checking lines 35-45 of .env file:"
sed -n '35,45p' .env 2>/dev/null || sed -n '35,45p' backend/.env 2>/dev/null
echo ""
echo "Searching for lines with spaces in keys:"
grep -n "^[A-Z_]* " .env 2>/dev/null || grep -n "^[A-Z_]* " backend/.env 2>/dev/null
echo ""
echo "=== End Diagnosis ==="
