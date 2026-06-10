# GitHub Repository Cleanup Policy

## 1. Goal

The GitHub repository must look and behave like the source home of a commercial
product.

It must not look like:

- a patch archive for another product;
- a public-copy workspace;
- an external repo mirror;
- a demo folder;
- a one-off server notebook.

## 2. Keep

Keep:

- source code owned by this product;
- tests;
- current product documentation;
- deployment scripts that belong to the new product path;
- CI workflows;
- configuration templates without secrets;
- license file.

## 3. Remove

Remove:

- external application source mirrors;
- old patch overlay directories;
- generated export folders;
- old public brief packs;
- legacy static pages not used by the product;
- outdated deployment scripts that point to old paths;
- probe scripts for retired runtimes;
- historical phase reports that compete with the current mature-source-first
  baseline;
- runtime data, logs, sessions, QR state, and media.

## 4. Quarantine Rule

If an external project is still useful, do not copy it into this repository.

Use one of:

- separate checkout outside the product repo;
- Git submodule only after license review;
- container image reference;
- documented adapter contract;
- documented evidence in current docs or release notes.

## 5. Documentation Rule

Current docs live in `docs/`.

Do not keep multiple competing architecture documents. When the architecture
changes, update the current functional docs directly.

## 6. Deployment Rule

The current deployment path is:

- `docker-compose.production.yml`;
- `scripts/deploy-usable.ps1`;
- `scripts/deploy-usable.sh`;
- `docs/12-one-click-deployment.md`.

Do not add a second production deployment path unless the old one is retired or
clearly marked as development-only.

## 7. Clean Repository Acceptance

The repository is clean when:

- `git status` shows only intentional source, docs, tests, and config changes;
- no external mirror folders are present;
- no old patch archive is tracked;
- no public-copy pack is tracked;
- no runtime data or logs are tracked;
- repository hygiene check passes;
- CI passes;
- README points only to current docs.
