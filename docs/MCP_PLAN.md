# Plan to Add MCP Server Mode

This document outlines the steps to add a Model Context Protocol (MCP) server mode to the project.

1.  **Add MCP Dependency**: Add the `mcp` library to `pyproject.toml` to include the necessary dependencies for building an MCP server.
2.  **Create MCP Server File**: Create a new file, `src/ccp/mcp_server.py`, to contain the logic for the MCP server.
3.  **Implement `run_model` Tool**: In the new file, implement a tool named `run_model` that programmatically accesses the existing model-switching logic.
4.  **Integrate into CLI**: Add a new `mcp` command to `src/ccp/cli.py` to allow starting the project in MCP server mode.
