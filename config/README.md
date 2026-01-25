# Configuration Directory

This directory contains configuration files for various tools and services.

## Files

- `.npmrc` - NPM configuration file
- `.mcphost.json` - MCP (Model Context Protocol) host configuration

## Usage

These configuration files are automatically used by their respective tools when present in the project root. They have been moved here for better organization but may need to be symlinked back to the root if the tools don't support configuration in subdirectories.

## Notes

- `.npmrc` - Contains NPM registry and authentication settings
- `.mcphost.json` - Configuration for MCP server hosting