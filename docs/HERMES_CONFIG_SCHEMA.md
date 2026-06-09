# Hermes Config Schema

Technical path source: https://github.com/LUTAO581314/hermes-

Hermes runtime settings are exposed through a secret-safe writable schema.
Brain UI should render settings from the schema instead of hard-coding every
field.

## Endpoints

```text
GET /config/schema
POST /config/update
```

`GET /config/schema` returns grouped fields for:

- model gateway,
- search intelligence,
- media and sticker generation,
- social performance budgets.

`POST /config/update` accepts:

```json
{
  "updates": {
    "HERMES_AI_FAST_MODEL": "5.4-mini",
    "HERMES_SOCIAL_FAST_REPLY_TARGET_MS": 5000
  }
}
```

## Guardrails

- Only whitelisted keys are writable.
- Unknown keys are rejected.
- Secret values are never returned by schema or update responses.
- Secret fields only expose `configured: true|false`.
- Empty secret updates keep the existing value.
- Host, port, filesystem paths, safe mode, and other high-risk runtime keys are
  not writable through the first schema.

## Env File

The runtime writes to:

```text
HERMES_CONFIG_ENV_PATH
```

If that variable is not set, it writes to:

```text
.env.hermes-runtime
```

The update helper preserves comments and unrelated keys, updates existing
whitelisted keys, and appends missing whitelisted keys.

After a successful update, the current runtime process updates `os.environ` and
reloads its `RuntimeConfig`, so the next `/health`, `/performance`, or
`/config/schema` response reflects the saved values.

## Frontend Rendering Contract

Brain UI should:

1. Read `GET /frontend/contract`.
2. Discover `endpoints.config_schema.path`.
3. Render groups and fields from `GET /config/schema`.
4. Send changed values to `POST /config/update`.
5. For secret fields, show only configured state and an empty password input.

Do not store raw secrets in local storage, chat messages, event streams, public
job records, logs, or screenshots.
