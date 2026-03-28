# Configuration Directory

This directory contains configuration files for various tools and services.

## Files

- `superset/` - Apache Superset configuration

Inside `superset/`:

- `superset_config.py` - Superset runtime configuration and branding
- `superset_init.py` - Best-effort bootstrap script executed by the Superset container after `superset init`

## Notes

Runtime tool config files that must be in project root (for example `.npmrc` and `.mcphost.json`) are intentionally kept at the repository root.