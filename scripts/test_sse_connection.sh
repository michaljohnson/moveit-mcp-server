#!/bin/bash
# Test script to verify SSE endpoint is working

echo "Testing MCP Server SSE endpoint..."
echo ""

echo "1. Testing GET /sse (should establish SSE connection):"
curl -v -N -H "Accept: text/event-stream" http://localhost:8000/sse &
CURL_PID=$!
sleep 2
kill $CURL_PID 2>/dev/null

echo ""
echo ""
echo "2. Testing POST /messages (should accept messages):"
curl -v -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

echo ""
echo ""
echo "If you see '200 OK' responses, the server is configured correctly."
