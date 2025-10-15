# Claude Code MCP Configuration

## Correct Configuration for SSE Transport

The MCP server exposes two endpoints:
- `GET /sse` - Establishes the SSE connection
- `POST /messages` - Sends messages to the server

### Configuration in Claude Code

Try these configuration formats:

**Format 1: Simple URL**
```json
{
  "mcpServers": {
    "moveit-mcp-server": {
      "url": "http://localhost:8000/sse"
    }
  }
}
```

**Format 2: Explicit type (Recommended for Claude Desktop)**
```json
{
  "mcpServers": {
    "moveit-mcp-server": {
      "type": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

## Testing the Endpoints

Test if the server is responding correctly:

```bash
# Test SSE connection (should keep connection open)
curl -N -H "Accept: text/event-stream" http://localhost:8000/sse

# Test POST to messages (will fail without session, but shouldn't crash)
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"test"}'
```

## Common Issues

### "Received request without session_id"
This means Claude Code is trying to POST before establishing a GET connection. This is normal during the initial handshake. If it persists, check:
1. The URL in Claude Code config points to the correct endpoint
2. The server is running and accessible
3. No proxy/firewall is interfering with the connection

### "405 Method Not Allowed"
- GET requests should go to `/sse`
- POST requests should go to `/messages`

If you see POST to `/sse`, update your Claude Code configuration.
