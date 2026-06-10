# Hermes Runtime Source

This directory contains the bairui/Hermes runtime source.

The runtime is mature-source-first: use existing Hermes/vendor runtime code
where it reduces product risk, preserve upstream attribution and licenses, and
add bairui product behavior through clear adapters, deployment scripts,
readiness checks, CLI commands, tests, and platform contracts.

Current CLI entrypoint:

```bash
python -m src.hermes --help
python -m src.hermes status
python -m src.hermes serve
```

Productization order:

1. configuration and environment loading;
2. PostgreSQL migrations;
3. health and readiness API;
4. license loading;
5. admin initialization;
6. model gateway;
7. job and audit system;
8. Obsidian write pipeline;
9. deployment and backup commands.
