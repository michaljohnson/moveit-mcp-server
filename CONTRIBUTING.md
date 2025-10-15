# Contributing to MoveIt2 MCP Server

Thank you for your interest in contributing to the MoveIt2 MCP Server!

## Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd moveit2-mcp-server
   ```

2. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Setup ROS2 and MoveIt2**
   - Follow the [MoveIt2 installation guide](https://moveit.picknik.ai/)
   - Ensure `moveit_py` is installed

## Code Style

- Follow PEP 8 guidelines
- Use `black` for formatting: `black src/`
- Use `ruff` for linting: `ruff check src/`
- Add type hints where applicable
- Write docstrings for all public functions

## Testing

Before submitting a PR:

1. Test with the example client:
   ```bash
   python examples/test_client.py
   ```

2. Ensure all tools work correctly
3. Check that error handling is appropriate

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with clear commit messages
3. Update documentation if needed
4. Test your changes thoroughly
5. Submit a PR with a clear description

## Adding New Tools

To add a new MCP tool:

1. Add the implementation in the appropriate file under `src/moveit_mcp/tools/`
2. Register the tool in the corresponding `register_*_tools` function
3. Add tool schema to the `list_tools()` handler
4. Update README.md with the new tool
5. Add example usage in `examples/`

## Adding New Resources

To add a new resource:

1. Add URI pattern to `list_resources()` in `src/moveit_mcp/resources/providers.py`
2. Implement the resource reader in `read_resource()`
3. Update README.md documentation

## Reporting Issues

- Use GitHub Issues
- Provide clear reproduction steps
- Include ROS2 distro and MoveIt2 version
- Include relevant log output

## Questions?

Open a GitHub Discussion or Issue for questions.
