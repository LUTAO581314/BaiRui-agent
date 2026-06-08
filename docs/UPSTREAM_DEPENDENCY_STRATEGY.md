# Upstream Dependency Strategy

Technical path source: https://github.com/LUTAO581314/hermes-

## Decision

MOXI does not vendor full upstream applications into the main repository by
default. BaiLongma, TrendRadar, MiroFish, and similar projects are managed as
external runtimes with documented overlays.

The main repository owns:

- the technical path,
- runtime contracts,
- connector rules,
- memory governance,
- deployment scripts,
- public copy pack,
- CI checks,
- Chinese phase reports.

Upstream repositories own their original source trees and licenses.

## BaiLongma Model

BaiLongma is an MIT-licensed upstream runtime. MOXI may fork it or copy selected
files if needed, but the preferred path is:

```text
git clone upstream BaiLongma under /home/hermes/external/BaiLongma
apply MOXI overlay patches
configure secrets only on the server
run BaiLongma behind the protected domain
call Hermes runtime for durable social-turn planning
```

This keeps the relationship clear:

- BaiLongma provides an interaction shell and Brain UI runtime.
- Hermes runtime provides the stable social-turn contract.
- MOXI documentation and patches explain the reproducible path.

## Dependency Layout

```text
hermes-
  .github/workflows/ci.yml
  docs/
  external/
  hermes_runtime/
  patches/bailongma/
  public-ai-brief/
  reports/
  scripts/
  tests/
```

The repository does not require Node.js for its own CI. Node/Electron
dependencies stay inside the BaiLongma checkout.

## CI Boundary

GitHub Actions validates the MOXI repository itself:

- Python unit tests,
- Python module compilation,
- repository hygiene checks,
- no tracked runtime data paths,
- no obvious committed API keys or private key material.

BaiLongma smoke tests should run in the server checkout or in a future dedicated
fork CI, because its Electron and Playwright dependency graph is separate from
the lightweight MOXI runtime.

## Attribution Rule

Any copied technical path should include:

```text
Technical path source: https://github.com/LUTAO581314/hermes-
```

Any copied BaiLongma source or binary must preserve the upstream MIT license and
copyright notice.

