# Server Rebuild And Deployment

## 1. Rebuild Decision

The server should be rebuilt around the production architecture instead of
continuing to accumulate temporary services.

The rebuilt server must provide:

- Hermes backend runtime;
- PostgreSQL database;
- Nginx reverse proxy;
- optional Docker Compose service management;
- systemd service fallback;
- isolated external runtimes;
- Obsidian vault storage;
- backups;
- logs and audit export;
- clear secret management.

Production has only two supported deployment modes:

- Local production environment: the product runs on a local workstation, private
  mini server, NAS, or LAN machine. It is a real production instance for the
  owner. It does not require a public domain, public DNS, or public callback
  route. Public-platform callbacks must stay disabled unless a reviewed tunnel
  or gateway is added later.
- Domain server production environment: the product runs on a server with a
  domain name, DNS resolution, HTTPS, and Nginx routes. This mode is required
  for stable Feishu callbacks, WeChat callbacks, QQ callbacks, remote Brain UI,
  and any internet-facing access.

## 2. Target Server Layout

```text
/opt/moxi-os/
  app/
    hermes/
    frontend/
  config/
    hermes.env
    postgres.env
    nginx/
  data/
    postgres/
    hermes/
    everos/
    obsidian-vault/
    trendaradar-output/
    simulations/
  logs/
    hermes/
    nginx/
    postgres/
  backups/
  releases/
  scripts/
```

Use `/opt/moxi-os` for the rebuilt product path. Do not continue mixing
production services into temporary historical folders.

For local production on Windows or a desktop machine, use an equivalent fixed product path,
for example:

```text
D:\moxi-os\
  app\
  config\
  data\
  logs\
  backups\
```

The path may differ by operating system, but it must be stable, backed up, and
separated from temporary development checkouts.

## 3. Core Services

| Service | Bind | Purpose |
| --- | --- | --- |
| Hermes | `127.0.0.1:8787` | Backend authority |
| PostgreSQL | local socket / private port | Production database |
| Nginx | `443` | Public HTTPS entry |
| EverOS | `127.0.0.1:8000` | Automatic memory engine |
| TrendRadar | private local port or MCP | Trend runtime |
| SearXNG | private local port, optional | Metasearch |
| MiroFish | private local port or on-demand worker | Simulation |

Only Nginx should be publicly exposed.

In local production environment, Nginx is optional. The default is:

```text
http://127.0.0.1:8787        -> Hermes API
http://127.0.0.1:<frontend>  -> MOXI / Brain UI
PostgreSQL local socket or private localhost port
```

In domain server production environment, Nginx is required:

```text
https://your-domain.example/       -> MOXI / Brain UI
https://your-domain.example/api/   -> Hermes API
https://your-domain.example/admin/ -> protected admin surface
```

## 4. Rebuild Sequence

1. Choose deployment mode: local production environment or domain server
   production environment.
2. Snapshot the current server or local production machine.
3. Export current `.env`, Nginx config, systemd units, Obsidian vault, and logs
   required for audit.
4. Create `/opt/moxi-os` or the local-production equivalent path.
5. Install PostgreSQL and create the production database.
6. Deploy Hermes from the current repository source.
7. Run database migrations.
8. Deploy MOXI / Brain UI static or frontend build output.
9. Configure Nginx routes when domain server production environment is selected.
10. Start EverOS as an internal service.
11. Attach TrendRadar as an external runtime.
12. Add SearXNG only if required.
13. Add MiroFish as on-demand simulation runtime.
14. Run smoke checks.
15. Switch protected domain traffic to the rebuilt stack when DNS is used.
16. Disable any legacy external backend after replacement checks pass.

## 5. Nginx Route Model

This section applies only to domain server production environment.

```text
https://domain/
  /                  -> MOXI / Brain UI
  /api/              -> Hermes
  /health-public     -> limited public health
  /social/feishu/*   -> Feishu callback allowlist path
  /admin/*           -> protected admin UI
```

Callbacks that require platform access must bypass user Basic Auth only on the
exact callback route. Admin pages and runtime APIs must remain protected.

For local production environment, callback-dependent features must be marked
`missing_config` or `disabled` unless an explicitly reviewed tunnel, relay, or
private gateway is configured.

## 6. Verification

The rebuilt server is accepted only when:

- `/health` returns ok;
- `/ready` returns ready;
- PostgreSQL migration status is current;
- Hermes can create and fetch one job;
- Hermes can write one audit event;
- Brain UI can read `/frontend/contract`;
- Obsidian vault path exists;
- EverOS health check passes;
- TrendRadar integration is visible;
- Feishu callback challenge path works;
- local production environment correctly disables or marks public callback
  features as unavailable;
- domain server production environment has working domain resolution and HTTPS;
- no raw secrets appear in Git, frontend output, reports, or logs.
