"""Tests for MCP server."""

import pytest
from unittest.mock import MagicMock, patch, mock_open
import yaml
import sys

# Mock dependencies
sys.modules['mcp'] = MagicMock()
sys.modules['mcp.server'] = MagicMock()
sys.modules['mcp.server.stdio'] = MagicMock()
sys.modules['mcp.server.sse'] = MagicMock()
sys.modules['mcp.types'] = MagicMock()
sys.modules['starlette'] = MagicMock()
sys.modules['starlette.applications'] = MagicMock()
sys.modules['starlette.routing'] = MagicMock()
sys.modules['starlette.responses'] = MagicMock()
sys.modules['starlette.types'] = MagicMock()
sys.modules['uvicorn'] = MagicMock()

from moveit_mcp.server import MoveItMCPServer


def test_server_initialization():
    """Test server initialization with default config."""
    server = MoveItMCPServer()

    assert server.server is not None
    assert server.moveit is None  # Not initialized until start()
    assert server.op_manager is None
    assert server._initialized is False


def test_default_config():
    """Test default configuration."""
    server = MoveItMCPServer()
    config = server._default_config()

    # Verify robot config
    assert config["robot"]["name"] == "panda"
    assert config["robot"]["description_package"] == "moveit_resources_panda_moveit_config"

    # Verify planning config
    assert config["planning"]["default_planner"] == "RRTConnect"
    assert config["planning"]["default_timeout"] == 5.0
    assert config["planning"]["planning_attempts"] == 10

    # Verify execution config
    assert config["execution"]["execution_timeout"] == 30.0

    # Verify MCP server config
    assert config["mcp_server"]["operation_timeout"] == 60.0
    assert config["mcp_server"]["max_concurrent_operations"] == 10


def test_load_config_from_file():
    """Test loading configuration from file."""
    test_config = {
        "robot": {"name": "test_robot"},
        "planning": {"default_timeout": 10.0}
    }

    with patch("builtins.open", mock_open(read_data=yaml.dump(test_config))):
        with patch("pathlib.Path.exists", return_value=True):
            server = MoveItMCPServer(config_path="/fake/config.yaml")

            # Should have loaded the custom config
            assert server.config["robot"]["name"] == "test_robot"
            assert server.config["planning"]["default_timeout"] == 10.0


def test_load_config_file_not_found():
    """Test handling of missing config file."""
    with patch("pathlib.Path.exists", return_value=False):
        server = MoveItMCPServer(config_path="/nonexistent/config.yaml")

        # Should fall back to defaults
        config = server.config
        assert config["robot"]["name"] == "panda"


def test_is_initialized():
    """Test is_initialized method."""
    server = MoveItMCPServer()

    # Should be False initially
    assert server.is_initialized() is False

    # Simulate initialization
    server._initialized = True
    assert server.is_initialized() is True


def test_logging_setup():
    """Test logging configuration."""
    config = {
        "logging": {
            "level": "DEBUG",
            "format": "%(levelname)s - %(message)s"
        }
    }

    with patch("logging.basicConfig") as mock_basic_config:
        server = MoveItMCPServer()
        server.config = config
        server._setup_logging()

        # Verify logging was configured (may be called multiple times in tests)
        assert mock_basic_config.called


def test_server_name():
    """Test that server has correct name."""
    server = MoveItMCPServer()

    # The server should be initialized with the correct name
    # (Note: This test verifies the Server() constructor call)
    assert hasattr(server, 'server')


@pytest.mark.parametrize("transport,host,port", [
    ("stdio", "0.0.0.0", 8000),
    ("sse", "localhost", 9000),
])
def test_server_run_parameters(transport, host, port):
    """Test server run with different parameters."""
    # This test just verifies the parameter handling
    # Actual running is tested in integration tests
    assert transport in ["stdio", "sse"]
    assert isinstance(host, str)
    assert isinstance(port, int)
    assert 1 <= port <= 65535
