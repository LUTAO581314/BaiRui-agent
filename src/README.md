# Hermes Runtime Source

This directory is reserved for the rebuilt Hermes runtime source.

The previous prototype implementation has been removed. New source code must be
implemented from the current product, architecture, database, memory, deployment,
and commercial delivery documents under `docs/`.

Initial rebuild order:

1. configuration and environment loading;
2. PostgreSQL migrations;
3. health and readiness API;
4. license loading;
5. admin initialization;
6. model gateway;
7. job and audit system;
8. Obsidian write pipeline;
9. deployment and backup commands.
