# Claude Code MCP Configuration

## Transport Options

The MCP server supports three transport modes:

| Transport | Flag | Use Case |
|-----------|------|----------|
| `stdio` | `--transport stdio` | Local execution, default |
| `sse` | `--transport sse` | Legacy HTTP/SSE (deprecated MCP spec) |
| `http` | `--transport http` | Streamable HTTP (MCP spec 2025-03-26, recommended) |

---

## Streamable HTTP Transport (Recommended)

The `http` transport implements the current MCP specification (2025-03-26) using a single `/mcp` endpoint.

### Start the server

```bash
moveit-mcp-server-wrapper --config config/panda_mcp_server.yaml --transport http --port 8001
```

### Configure in Claude Code / Claude Desktop

```json
{
  "mcpServers": {
    "moveit-mcp-server": {
      "type": "http",
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

### Test the endpoint

```bash
# Health check
curl http://localhost:8001/

# MCP endpoint (POST with JSON-RPC)
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{}}}'
```

---

## SSE Transport (Legacy)

The `sse` transport uses two endpoints: `GET /sse` for the event stream and `POST /messages` for client messages.

### Start the server

```bash
moveit-mcp-server-wrapper --config config/panda_mcp_server.yaml --transport sse --port 8000
```

### Configure in Claude Code / Claude Desktop

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

### Test the endpoints

```bash
# Test SSE connection (should keep connection open)
curl -N -H "Accept: text/event-stream" http://localhost:8000/sse

# Test POST to messages (will fail without session, but shouldn't crash)
curl -X POST http://localhost:8000/messages \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"test"}'
```

---

## Common Issues

### "Received request without session_id" (SSE transport)
Normal during initial handshake. If it persists, check:
1. The URL points to `/sse`, not `/messages`
2. The server is running and accessible
3. No proxy/firewall is interfering

### "405 Method Not Allowed" (SSE transport)
- GET requests → `/sse`
- POST requests → `/messages`

### Connection refused
1. Verify the server is running: `curl http://localhost:8000/`
2. Check the port is exposed: `docker ps`
3. With `network_mode: host`, the port should be directly accessible
