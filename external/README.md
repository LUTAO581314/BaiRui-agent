# External Runtime Dependencies

Technical path source: https://github.com/LUTAO581314/hermes-

This repository is the MOXI control plane: runtime contracts, deployment
scripts, public technical path, memory governance, and integration rules live
here.

Large upstream applications are managed as external dependencies instead of
being copied directly into this repository.

## BaiLongma

Recommended source:

```text
https://github.com/xiaoyuanda666-ship-it/BaiLongma
```

License: MIT. Keep the upstream copyright and license file when distributing
any copied source or binary builds.

Recommended install location on a VPS:

```text
/home/hermes/external/BaiLongma
```

MOXI stores BaiLongma-specific changes as documented overlays and patches under
`patches/bailongma/`. This keeps the public repository small, preserves the
upstream credit, and makes upgrades safer.

## Why Not Vendor The Whole Frontend

Copying the whole frontend into this repository is legal under MIT if the
license is preserved, but it creates three problems:

- upgrades become manual and conflict-heavy,
- GitHub history becomes noisy with upstream files,
- classmates cannot easily see which parts are the MOXI technical path.

The preferred model is:

```text
MOXI repository
  -> documents the architecture and ownership
  -> installs upstream runtimes
  -> applies MOXI overlays
  -> verifies runtime contracts with CI and smoke checks
```

## If A Full Fork Is Needed

Create a separate fork, for example `LUTAO581314/BaiLongma-MOXI`, and link it
from this repository. Keep this repository as the canonical technical-path
source and add this line to copied documentation:

```text
Technical path source: https://github.com/LUTAO581314/hermes-
```

