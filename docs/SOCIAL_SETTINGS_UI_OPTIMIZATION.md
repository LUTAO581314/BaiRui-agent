# Social Settings UI Optimization

Technical path source: https://github.com/LUTAO581314/hermes-

## 1. Current Problems From The Screenshot

The current social settings panel works, but it is hard to operate when more
channels are added.

Problems:

- channels are stacked vertically in one long scroll area,
- status is shown as text instead of actionable diagnostics,
- WeChat, Feishu, WeCom, and future QQ are not visually equal channels,
- there is no QQ entry,
- test connection, copy webhook, and credential validation are not grouped,
- the primary save action is too far from the fields,
- the modal is visually heavy and low-information-density at the same time.

## 2. Recommended Layout

Use a two-level settings layout:

```text
Social Media
  -> Channel overview
  -> Feishu
  -> WeCom
  -> WeChat ClawBot
  -> QQ Official Bot
  -> Runtime Connector
```

The first screen should be a channel overview grid:

| Channel | Status | Primary action |
| --- | --- | --- |
| Feishu | connected / missing / error | Test webhook |
| WeCom | missing credentials | Configure |
| WeChat ClawBot | connected | Reconnect / disconnect |
| QQ Official Bot | missing credentials | Configure |

Then each channel gets its own detail panel instead of one huge mixed form.

## 3. Channel Card Contract

Each channel card should show:

- icon or channel mark,
- channel name,
- status chip,
- last check timestamp,
- missing fields count,
- primary action,
- secondary action menu.

Status chips:

- `Connected`
- `Missing credentials`
- `Needs scan`
- `Webhook blocked`
- `Auth failed`
- `Disabled`

## 4. QQ Card Fields

QQ Official Bot should include:

- Mode: disabled / official bot / planned custom bridge,
- App ID,
- Bot Token,
- Bot Secret,
- Webhook Token,
- Webhook URL copy button,
- Test Connection,
- Save,
- Reset.

All secret fields should show:

- `Configured` when present,
- `Missing` when empty,
- never the raw value.

## 5. Runtime Connector Section

Add a separate runtime connector section because server calls may require
authentication.

Fields:

- Runtime Base URL,
- Basic Auth User,
- Basic Auth Password,
- Test Runtime,
- Last response status,
- Last error.

This directly fixes the 401 problem: the UI should make it obvious whether the
connector is calling localhost, a protected server URL, or a missing runtime.

## 6. Interaction Rules

- `Save all` remains sticky at the bottom right.
- Each channel also has a local `Save channel` button.
- `Test` buttons run without saving raw secrets to logs.
- Failure messages should explain the next action:
  - 401: Basic Auth missing or wrong.
  - 403: webhook token invalid.
  - 404: route not deployed.
  - 502: upstream service down.
  - timeout: runtime unreachable.
- Avoid long explanatory text inside the UI; move details to tooltips or docs.

## 7. Visual Direction

Keep the dark operational theme, but make it denser and clearer:

- use channel cards with 8px radius,
- replace long text blocks with status chips,
- use segmented controls for mode,
- use icon buttons for copy/test/reconnect,
- keep the left nav but add a right-side sticky status summary,
- make the scroll area clearer with section headers and local actions.

## 8. Implementation Order

1. Add QQ Official Bot config model and health status.
2. Add channel overview cards.
3. Split channel detail forms.
4. Add runtime connector auth panel.
5. Add test buttons and error mapping.
6. Add sticky save bar.
7. Add mobile layout with single-column channel cards.
