# Tests

This directory is reserved for the rebuilt Hermes test suite.

The previous tests were removed with the old runtime implementation. New tests
should be added alongside the rebuilt runtime, starting with:

- configuration loading;
- PostgreSQL migration checks;
- health and readiness API;
- license validation;
- audit log writes;
- Obsidian write pipeline;
- deployment smoke checks.
